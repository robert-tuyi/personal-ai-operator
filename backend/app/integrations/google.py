"""Gmail + Google Calendar integration.

Read helpers fetch context for the brief and drafts. The write helpers (_send_email,
_create_event) are the *executors* for approved actions — they are registered with the
approval chokepoint and must only ever be invoked through it, never called directly.

All calls go to Google's REST APIs over httpx using the owner's stored OAuth access token
(resolved/refreshed by integrations.google_oauth). Everything is owner-scoped (ADR 0003).
"""

import base64
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

import httpx
from sqlmodel import Session

from app.core import approval
from app.domain.actions import ActionType
from app.integrations.google_oauth import access_token_for
from app.services import memory

GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _header(headers: list[dict], name: str) -> str:
    """Pull a header value out of a Gmail message's metadata headers."""
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


# --- Read helpers -----------------------------------------------------------------------


def list_recent_messages(session: Session, *, owner_id: str, limit: int = 20) -> list[dict]:
    """Recent inbox messages as light dicts: {id, sender, subject, snippet}.

    Metadata only — we never pull whole message bodies into the brief (cost discipline).
    """
    token = access_token_for(session, owner_id=owner_id)
    headers = _auth_headers(token)

    listing = httpx.get(
        f"{GMAIL_BASE}/messages",
        headers=headers,
        params={"maxResults": limit, "labelIds": "INBOX"},
        timeout=30.0,
    )
    listing.raise_for_status()
    ids = [m["id"] for m in listing.json().get("messages", [])]

    messages: list[dict] = []
    for msg_id in ids:
        detail = httpx.get(
            f"{GMAIL_BASE}/messages/{msg_id}",
            headers=headers,
            params={
                "format": "metadata",
                "metadataHeaders": ["From", "Subject"],
            },
            timeout=30.0,
        )
        detail.raise_for_status()
        data = detail.json()
        hdrs = data.get("payload", {}).get("headers", [])
        messages.append(
            {
                "id": data.get("id"),
                "sender": _header(hdrs, "From"),
                "subject": _header(hdrs, "Subject"),
                "snippet": data.get("snippet", ""),
            }
        )
    return messages


def list_sent_threads(session: Session, *, owner_id: str, limit: int = 20) -> list[dict]:
    """Recent threads with a sent message, last-message-only metadata: {thread_id, subject,
    last_from, last_to, last_sent_at}. Used by the follow-up engine (services/followups.py)
    to find threads still awaiting a reply.

    Bounded to `limit` threads — never scans the whole sent history (cost discipline).
    """
    token = access_token_for(session, owner_id=owner_id)
    headers = _auth_headers(token)

    listing = httpx.get(
        f"{GMAIL_BASE}/threads",
        headers=headers,
        params={"maxResults": limit, "q": "in:sent"},
        timeout=30.0,
    )
    listing.raise_for_status()
    thread_ids = [t["id"] for t in listing.json().get("threads", [])]

    threads: list[dict] = []
    for thread_id in thread_ids:
        detail = httpx.get(
            f"{GMAIL_BASE}/threads/{thread_id}",
            headers=headers,
            params={
                "format": "metadata",
                "metadataHeaders": ["From", "To", "Subject"],
            },
            timeout=30.0,
        )
        detail.raise_for_status()
        data = detail.json()
        messages = data.get("messages", [])
        if not messages:
            continue
        last = messages[-1]
        hdrs = last.get("payload", {}).get("headers", [])
        threads.append(
            {
                "thread_id": data.get("id"),
                "subject": _header(hdrs, "Subject"),
                "last_from": _header(hdrs, "From"),
                "last_to": _header(hdrs, "To"),
                "last_sent_at": datetime.fromtimestamp(int(last["internalDate"]) / 1000, tz=UTC),
            }
        )
    return threads


def todays_events(session: Session, *, owner_id: str) -> list[dict]:
    """Today's calendar events as light dicts: {id, title, start, end}."""
    token = access_token_for(session, owner_id=owner_id)

    now = datetime.now(UTC)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    resp = httpx.get(
        f"{CALENDAR_BASE}/calendars/primary/events",
        headers=_auth_headers(token),
        params={
            "timeMin": start_of_day.isoformat(),
            "timeMax": end_of_day.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
        },
        timeout=30.0,
    )
    resp.raise_for_status()

    events: list[dict] = []
    for item in resp.json().get("items", []):
        start = item.get("start", {})
        end = item.get("end", {})
        events.append(
            {
                "id": item.get("id"),
                "title": item.get("summary", "(untitled)"),
                "start": start.get("dateTime") or start.get("date"),
                "end": end.get("dateTime") or end.get("date"),
            }
        )
    return events


# --- Write executors (invoked ONLY by approval.execute_approved) ------------------------


def _send_email(payload: dict, ctx: approval.ExecutionContext) -> None:
    """Send an email via the Gmail API. Invoked only by approval.execute_approved.

    payload shape (from DraftReply / queue_send): {to, subject, body}.
    """
    token = access_token_for(ctx.session, owner_id=ctx.owner_id)

    msg = EmailMessage()
    msg["To"] = payload["to"]
    msg["Subject"] = payload.get("subject", "")
    msg.set_content(payload.get("body", ""))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    resp = httpx.post(
        f"{GMAIL_BASE}/messages/send",
        headers=_auth_headers(token),
        json={"raw": raw},
        timeout=30.0,
    )
    resp.raise_for_status()

    # Record what was actually sent (Phase 2 memory layer, ADR 0004) — never on draft or
    # proposal, only once the send has really happened.
    memory.write_memory(
        ctx.session,
        owner_id=ctx.owner_id,
        content=payload.get("body", ""),
        source="sent_email",
    )


def _create_event(payload: dict, ctx: approval.ExecutionContext) -> None:
    """Create a calendar event via the Calendar API. Invoked only by approval.execute_approved.

    payload shape: {title, start, end, attendees?, description?}. start/end are RFC3339
    datetimes.
    """
    token = access_token_for(ctx.session, owner_id=ctx.owner_id)

    body: dict = {
        "summary": payload.get("title", ""),
        "start": {"dateTime": payload["start"]},
        "end": {"dateTime": payload["end"]},
    }
    if payload.get("description"):
        body["description"] = payload["description"]
    if payload.get("attendees"):
        body["attendees"] = [{"email": a} for a in payload["attendees"]]

    resp = httpx.post(
        f"{CALENDAR_BASE}/calendars/primary/events",
        headers=_auth_headers(token),
        json=body,
        timeout=30.0,
    )
    resp.raise_for_status()


def register_action_executors() -> None:
    """Wire side-effecting executors into the approval chokepoint. Called at app startup."""
    approval.register_executor(ActionType.SEND_EMAIL, _send_email)
    approval.register_executor(ActionType.CREATE_CALENDAR_EVENT, _create_event)
