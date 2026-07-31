"""Urgent-item detection for the daily brief: VIP-contact emails, explicitly urgent
language (LLM-classified), and stale (48h+) unanswered sent threads.

A finding becomes a proposed self-notification email — a normal SEND_EMAIL pending
action the user must still approve and execute themselves, same as any other send
(CLAUDE.md invariant #1: no outbound action without explicit human approval, no
exceptions carved out for "it's just going to yourself"). This module only detects and
describes; it never sends anything, and `maybe_propose_notification` only ever calls
`approval.propose`.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from app.core import approval
from app.db.models import PendingActionRow
from app.domain.actions import ActionType, PendingAction
from app.domain.urgency import UrgentItem
from app.integrations import llm
from app.services.followups import find_stale_threads

# find_stale_threads only compares whole elapsed days (see services/followups.py), so the
# requested 48-hour threshold is expressed as 2 days — the closest it can represent.
STALE_THREAD_DAYS = 2
# How long a proposed notification "counts" before another one may be proposed — bounds
# this to roughly once a day regardless of how often the brief is refreshed, without
# needing a new column/migration to track it.
DEDUP_WINDOW_HOURS = 20
NOTIFICATION_KIND = "urgent_notification"

Classifier = Callable[[str], str]
NowFn = Callable[[], datetime]


def _vip_matches(sender: str, vip_contacts: list[str]) -> bool:
    sender_lower = sender.lower()
    return any(vip.lower() in sender_lower for vip in vip_contacts if vip)


def _classify_urgent_language(messages: list[dict], *, classify: Classifier) -> set[str]:
    """Ask the model which message ids read as explicitly urgent/time-sensitive.

    Fails closed: any response that doesn't clearly name message ids yields no matches
    rather than guessing — a missed notification is far better than a bogus one.
    """
    if not messages:
        return set()
    known_ids = {m.get("id") for m in messages if m.get("id")}
    lines = [f"{m.get('id')}: {m.get('subject', '')} — {m.get('snippet', '')}" for m in messages]
    prompt = (
        "Which of these emails use explicitly urgent or time-sensitive language "
        '(e.g. "urgent", "ASAP", "action required", a hard deadline)? Reply with ONLY '
        'a comma-separated list of their ids, or "none".\n\n' + "\n".join(lines)
    )
    reply = classify(prompt)
    named = {token.strip() for token in reply.split(",")}
    return named & known_ids


def find_urgent_items(
    messages: list[dict],
    threads: list[dict],
    *,
    owner_email: str,
    vip_contacts: list[str],
    now: NowFn | None = None,
    classify: Classifier | None = None,
) -> list[UrgentItem]:
    classify = classify or llm.summarize  # cheap model — classification isn't draft quality
    urgent_language_ids = _classify_urgent_language(messages, classify=classify)

    items: list[UrgentItem] = []
    for m in messages:
        is_vip = _vip_matches(m.get("sender", ""), vip_contacts)
        is_urgent_language = m.get("id") in urgent_language_ids
        if not (is_vip or is_urgent_language):
            continue
        items.append(
            UrgentItem(
                reason="vip" if is_vip else "urgent_language",
                title=m.get("subject") or "(no subject)",
                detail=f"From {m.get('sender', '?')}",
            )
        )

    stale = find_stale_threads(
        threads,
        owner_email=owner_email,
        stale_after_days=STALE_THREAD_DAYS,
        now=now,
    )
    for t in stale:
        items.append(
            UrgentItem(
                reason="stale_thread",
                title=t.get("subject") or "(no subject)",
                detail=f"No reply in {t['days_waiting']}+ days",
            )
        )
    return items


def _already_notified_recently(
    session: Session, *, owner_id: str, now: NowFn | None = None
) -> bool:
    now = now or (lambda: datetime.now(UTC))
    cutoff = now() - timedelta(hours=DEDUP_WINDOW_HOURS)
    statement = select(PendingActionRow).where(
        PendingActionRow.owner_id == owner_id,
        PendingActionRow.type == ActionType.SEND_EMAIL,
        PendingActionRow.created_at >= cutoff,
    )
    return any(row.payload.get("kind") == NOTIFICATION_KIND for row in session.exec(statement))


def _build_notification_payload(items: list[UrgentItem], *, to: str, app_url: str) -> dict:
    lines = [f"- {i.title} ({i.reason.replace('_', ' ')}): {i.detail}" for i in items]
    count = len(items)
    plural = "s" if count != 1 else ""
    return {
        "to": to,
        "subject": f"[Personal AI Operator] {count} urgent item{plural} need attention",
        "body": "\n".join(lines) + f"\n\nOpen the app: {app_url}",
        "kind": NOTIFICATION_KIND,
    }


def maybe_propose_notification(
    session: Session,
    *,
    owner_id: str,
    messages: list[dict],
    threads: list[dict],
    owner_email: str,
    vip_contacts: list[str],
    app_url: str,
    now: NowFn | None = None,
    classify: Classifier | None = None,
) -> PendingAction | None:
    """Detect urgent items and propose a self-notification if any are found and one
    hasn't already been proposed within the dedup window. Returns the proposed action,
    or None if nothing was urgent or a notification was already queued recently."""
    if _already_notified_recently(session, owner_id=owner_id, now=now):
        return None

    items = find_urgent_items(
        messages,
        threads,
        owner_email=owner_email,
        vip_contacts=vip_contacts,
        now=now,
        classify=classify,
    )
    if not items:
        return None

    count = len(items)
    return approval.propose(
        session,
        owner_id=owner_id,
        type=ActionType.SEND_EMAIL,
        summary=f"Urgent items notification ({count} item{'s' if count != 1 else ''})",
        payload=_build_notification_payload(items, to=owner_email, app_url=app_url),
    )
