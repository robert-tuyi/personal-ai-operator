"""Gmail/Calendar wiring tests — fully mocked, never hits live Google APIs.

We mock the OAuth access-token resolution and httpx so we can assert the request shapes and
response parsing without credentials or network.
"""

import base64
from datetime import UTC, datetime, timedelta

import pytest

from app.core import approval
from app.domain.actions import ActionStatus, ActionType
from app.domain.drafts import IncomingMessage
from app.integrations import google
from app.services.drafts import draft_reply


@pytest.fixture(autouse=True)
def _fake_access_token(monkeypatch):
    """Pretend the owner has a valid token, so no real OAuth/refresh happens."""
    monkeypatch.setattr(google, "access_token_for", lambda *a, **k: "test-access-token")


@pytest.fixture(autouse=True)
def _stub_memory_write(monkeypatch):
    """These tests are about the Gmail API shape, not memory writing (covered separately
    below and in test_memory_service.py) — stub it out so no embedding call happens."""
    monkeypatch.setattr(google.memory, "write_memory", lambda *a, **k: None)


class _FakeResponse:
    def __init__(self, json_data: dict):
        self._json = json_data
        self.status_code = 200

    def json(self) -> dict:
        return self._json

    def raise_for_status(self) -> None:
        return None


# --- read helpers -----------------------------------------------------------------------


def test_list_recent_messages_parses_metadata(session, monkeypatch):
    listing = _FakeResponse({"messages": [{"id": "m1"}]})
    detail = _FakeResponse(
        {
            "id": "m1",
            "snippet": "hello there",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Alice <alice@example.com>"},
                    {"name": "Subject", "value": "Lunch?"},
                ]
            },
        }
    )
    responses = iter([listing, detail])
    monkeypatch.setattr(google.httpx, "get", lambda *a, **k: next(responses))

    messages = google.list_recent_messages(session, owner_id="owner", limit=5)

    assert messages == [
        {
            "id": "m1",
            "sender": "Alice <alice@example.com>",
            "subject": "Lunch?",
            "snippet": "hello there",
        }
    ]


def test_list_recent_messages_unescapes_html_entities_in_snippet(session, monkeypatch):
    """Gmail returns the snippet HTML-entity-encoded — the brief page renders it
    verbatim now (it used to only ever pass through an LLM paraphrase), so a literal
    "&#39;" must not leak into the UI."""
    listing = _FakeResponse({"messages": [{"id": "m1"}]})
    detail = _FakeResponse(
        {
            "id": "m1",
            "snippet": "that&#39;s the &quot;commute tax&quot;",
            "payload": {"headers": []},
        }
    )
    responses = iter([listing, detail])
    monkeypatch.setattr(google.httpx, "get", lambda *a, **k: next(responses))

    messages = google.list_recent_messages(session, owner_id="owner", limit=5)

    assert messages[0]["snippet"] == 'that\'s the "commute tax"'


def test_list_sent_threads_parses_last_message_metadata(session, monkeypatch):
    listing = _FakeResponse({"threads": [{"id": "t1"}]})
    detail = _FakeResponse(
        {
            "id": "t1",
            "messages": [
                {
                    "internalDate": "1000000000000",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "me@example.com"},
                            {"name": "To", "value": "bob@example.com"},
                            {"name": "Subject", "value": "Proposal"},
                        ]
                    },
                },
                {
                    "internalDate": "1000086400000",  # last message: 1 day later
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "me@example.com"},
                            {"name": "To", "value": "bob@example.com"},
                            {"name": "Subject", "value": "Re: Proposal"},
                        ]
                    },
                },
            ],
        }
    )
    responses = iter([listing, detail])
    monkeypatch.setattr(google.httpx, "get", lambda *a, **k: next(responses))

    threads = google.list_sent_threads(session, owner_id="owner", limit=5)

    assert len(threads) == 1
    assert threads[0]["thread_id"] == "t1"
    assert threads[0]["subject"] == "Re: Proposal"  # last message's headers, not the first
    assert threads[0]["last_from"] == "me@example.com"
    assert threads[0]["last_to"] == "bob@example.com"
    assert threads[0]["last_sent_at"].year == 2001  # epoch ms 1000086400000


def test_todays_events_parses_items(session, monkeypatch):
    resp = _FakeResponse(
        {
            "items": [
                {
                    "id": "e1",
                    "summary": "Standup",
                    "start": {"dateTime": "2026-06-14T09:00:00Z"},
                    "end": {"dateTime": "2026-06-14T09:15:00Z"},
                }
            ]
        }
    )
    monkeypatch.setattr(google.httpx, "get", lambda *a, **k: resp)

    events = google.todays_events(session, owner_id="owner")

    assert events == [
        {
            "id": "e1",
            "title": "Standup",
            "start": "2026-06-14T09:00:00Z",
            "end": "2026-06-14T09:15:00Z",
        }
    ]


def test_upcoming_events_requests_the_complementary_range(session, monkeypatch):
    """upcoming_events must query tomorrow onward, never re-including today (that's
    todays_events' job) — asserted via the actual timeMin/timeMax sent to Google."""
    captured: dict = {}

    def fake_get(url, *, headers, params, timeout):
        captured["params"] = params
        return _FakeResponse(
            {
                "items": [
                    {
                        "id": "e2",
                        "summary": "Offsite",
                        "start": {"dateTime": "2026-06-16T09:00:00Z"},
                        "end": {"dateTime": "2026-06-16T17:00:00Z"},
                    }
                ]
            }
        )

    monkeypatch.setattr(google.httpx, "get", fake_get)

    events = google.upcoming_events(session, owner_id="owner", days=7)

    assert events == [
        {
            "id": "e2",
            "title": "Offsite",
            "start": "2026-06-16T09:00:00Z",
            "end": "2026-06-16T17:00:00Z",
        }
    ]
    time_min = datetime.fromisoformat(captured["params"]["timeMin"])
    time_max = datetime.fromisoformat(captured["params"]["timeMax"])
    now = datetime.now(UTC)
    assert time_min.date() == (now + timedelta(days=1)).date()  # starts tomorrow
    assert (time_max - time_min).days == 7


# --- write executors --------------------------------------------------------------------


def test_send_email_executor_posts_raw_message(session, monkeypatch):
    captured: dict = {}

    def fake_post(url, *, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return _FakeResponse({"id": "sent-1"})

    monkeypatch.setattr(google.httpx, "post", fake_post)

    ctx = approval.ExecutionContext(session=session, owner_id="owner")
    google._send_email({"to": "bob@example.com", "subject": "Hi", "body": "Hello Bob"}, ctx)

    assert captured["url"].endswith("/messages/send")
    assert captured["headers"]["Authorization"] == "Bearer test-access-token"
    decoded = base64.urlsafe_b64decode(captured["json"]["raw"]).decode()
    assert "To: bob@example.com" in decoded
    assert "Subject: Hi" in decoded
    assert "Hello Bob" in decoded


def test_send_email_executor_writes_memory_of_what_was_sent(session, monkeypatch):
    monkeypatch.setattr(google.httpx, "post", lambda *a, **k: _FakeResponse({"id": "sent-1"}))

    captured: dict = {}
    monkeypatch.setattr(
        google.memory,
        "write_memory",
        lambda sess, **kwargs: captured.update(kwargs),
    )

    ctx = approval.ExecutionContext(session=session, owner_id="owner-1")
    google._send_email({"to": "bob@example.com", "subject": "Hi", "body": "Hello Bob"}, ctx)

    assert captured == {
        "owner_id": "owner-1",
        "content": "Hello Bob",
        "source": "sent_email",
    }


def test_send_email_executor_skips_memory_for_urgent_notifications(session, monkeypatch):
    """Regression: a system-generated self-notification isn't the user's own reply
    style and must not pollute future draft-style retrieval."""
    monkeypatch.setattr(google.httpx, "post", lambda *a, **k: _FakeResponse({"id": "sent-1"}))
    called = []
    monkeypatch.setattr(google.memory, "write_memory", lambda *a, **k: called.append(1))

    ctx = approval.ExecutionContext(session=session, owner_id="owner-1")
    google._send_email(
        {
            "to": "me@example.com",
            "subject": "Urgent items",
            "body": "- Thing one\n- Thing two",
            "kind": "urgent_notification",
        },
        ctx,
    )

    assert called == []


def test_create_event_executor_posts_event(session, monkeypatch):
    captured: dict = {}

    def fake_post(url, *, headers, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse({"id": "evt-1"})

    monkeypatch.setattr(google.httpx, "post", fake_post)

    ctx = approval.ExecutionContext(session=session, owner_id="owner")
    google._create_event(
        {
            "title": "Sync",
            "start": "2026-06-14T10:00:00Z",
            "end": "2026-06-14T10:30:00Z",
            "attendees": ["bob@example.com"],
        },
        ctx,
    )

    assert captured["url"].endswith("/calendars/primary/events")
    assert captured["json"]["summary"] == "Sync"
    assert captured["json"]["start"] == {"dateTime": "2026-06-14T10:00:00Z"}
    assert captured["json"]["attendees"] == [{"email": "bob@example.com"}]


# --- the chokepoint still owns execution ------------------------------------------------


def test_executor_runs_through_approval_chokepoint(session, monkeypatch):
    """End-to-end: an approved SEND_EMAIL action drives _send_email via execute_approved,
    and the invariant (no execution before approval) still holds."""
    posts: list[dict] = []
    monkeypatch.setattr(
        google.httpx, "post", lambda *a, **k: posts.append(k.get("json")) or _FakeResponse({})
    )

    google.register_action_executors()
    try:
        action = approval.propose(
            session,
            owner_id="owner",
            type=ActionType.SEND_EMAIL,
            summary="Send reply: Re: hello",
            payload={"to": "bob@example.com", "subject": "Re: hello", "body": "hi"},
        )

        # Unapproved -> must refuse, no API call.
        with pytest.raises(approval.ApprovalError):
            approval.execute_approved(session, owner_id="owner", action_id=action.id)
        assert posts == []

        approval.approve(session, owner_id="owner", action_id=action.id)
        executed = approval.execute_approved(session, owner_id="owner", action_id=action.id)

        assert executed.status == ActionStatus.EXECUTED
        assert len(posts) == 1  # the Gmail send happened exactly once, after approval
    finally:
        approval._executors.pop(ActionType.SEND_EMAIL, None)
        approval._executors.pop(ActionType.CREATE_CALENDAR_EVENT, None)


def test_draft_reply_round_trip_actually_sends(session, monkeypatch):
    """Regression test: a real draft_reply() output must carry enough to actually send once
    approved. Before the `to` field existed on DraftReply, this round trip failed at
    execution time with KeyError('to') — queue_send() passed draft.model_dump() straight
    through as the SEND_EMAIL payload, and it never carried a recipient."""
    posts: list[dict] = []
    monkeypatch.setattr(
        google.httpx, "post", lambda *a, **k: posts.append(k.get("json")) or _FakeResponse({})
    )

    message = IncomingMessage(
        id="m1", sender="alice@example.com", subject="Lunch?", body="Free at noon?"
    )
    draft = draft_reply(
        message,
        session=session,
        owner_id="owner",
        generate=lambda p: "Sure!",
        retrieve=lambda *a, **k: [],
    )

    google.register_action_executors()
    try:
        action = approval.propose(
            session,
            owner_id="owner",
            type=ActionType.SEND_EMAIL,
            summary=f"Send reply: {draft.subject}",
            payload=draft.model_dump(),
        )
        approval.approve(session, owner_id="owner", action_id=action.id)
        executed = approval.execute_approved(session, owner_id="owner", action_id=action.id)

        assert executed.status == ActionStatus.EXECUTED
        decoded = base64.urlsafe_b64decode(posts[0]["raw"]).decode()
        assert "To: alice@example.com" in decoded
    finally:
        approval._executors.pop(ActionType.SEND_EMAIL, None)
        approval._executors.pop(ActionType.CREATE_CALENDAR_EVENT, None)
