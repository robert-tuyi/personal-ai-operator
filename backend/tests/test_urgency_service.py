"""services/urgency.py tests. Gmail data, "now", and the classifier are all injected —
nothing here hits Gmail or an LLM. The dedup check touches the DB, so it uses the shared
in-memory `session` fixture (conftest.py)."""

from datetime import UTC, datetime, timedelta

from app.core import approval
from app.db.models import PendingActionRow
from app.domain.actions import ActionStatus, ActionType
from app.services import urgency


def _message(**overrides) -> dict:
    base = {
        "id": "m1",
        "sender": "Alice <alice@example.com>",
        "subject": "Quick question",
        "snippet": "Got a minute?",
    }
    return {**base, **overrides}


def _thread(**overrides) -> dict:
    base = {
        "thread_id": "t1",
        "subject": "Proposal",
        "last_from": "me@example.com",
        "last_to": "bob@example.com",
        "last_sent_at": datetime(2026, 7, 1, tzinfo=UTC),
    }
    return {**base, **overrides}


def _fixed_now(dt: datetime):
    return lambda: dt


def _no_urgent_language(_prompt: str) -> str:
    return "none"


# --- find_urgent_items -------------------------------------------------------------------


def test_find_urgent_items_flags_vip_sender():
    items = urgency.find_urgent_items(
        [_message(sender="Alice Boss <alice@example.com>")],
        [],
        owner_email="me@example.com",
        vip_contacts=["alice@example.com"],
        classify=_no_urgent_language,
    )

    assert len(items) == 1
    assert items[0].reason == "vip"


def test_find_urgent_items_flags_urgent_language_via_classifier():
    def classify(prompt: str) -> str:
        assert "m1" in prompt
        return "m1"

    items = urgency.find_urgent_items(
        [_message(id="m1")],
        [],
        owner_email="me@example.com",
        vip_contacts=[],
        classify=classify,
    )

    assert len(items) == 1
    assert items[0].reason == "urgent_language"


def test_find_urgent_items_ignores_classifier_ids_not_in_the_batch():
    """Fails closed: a hallucinated/unknown id from the model must never be trusted."""
    items = urgency.find_urgent_items(
        [_message(id="m1")],
        [],
        owner_email="me@example.com",
        vip_contacts=[],
        classify=lambda _prompt: "some-other-id",
    )

    assert items == []


def test_find_urgent_items_skips_non_vip_non_urgent_messages():
    items = urgency.find_urgent_items(
        [_message(sender="rando@example.com")],
        [],
        owner_email="me@example.com",
        vip_contacts=["alice@example.com"],
        classify=_no_urgent_language,
    )

    assert items == []


def test_find_urgent_items_flags_stale_sent_threads():
    items = urgency.find_urgent_items(
        [],
        [_thread()],
        owner_email="me@example.com",
        vip_contacts=[],
        now=_fixed_now(datetime(2026, 7, 4, tzinfo=UTC)),  # 3 days later, past the 48h/2d bar
        classify=_no_urgent_language,
    )

    assert len(items) == 1
    assert items[0].reason == "stale_thread"


def test_find_urgent_items_excludes_threads_not_yet_stale():
    items = urgency.find_urgent_items(
        [],
        [_thread()],
        owner_email="me@example.com",
        vip_contacts=[],
        now=_fixed_now(datetime(2026, 7, 1, 12, tzinfo=UTC)),  # 12h later
        classify=_no_urgent_language,
    )

    assert items == []


# --- maybe_propose_notification -----------------------------------------------------------


def test_maybe_propose_notification_proposes_a_pending_action(session):
    action = urgency.maybe_propose_notification(
        session,
        owner_id="owner-1",
        messages=[_message(sender="Alice Boss <alice@example.com>")],
        threads=[],
        owner_email="me@example.com",
        vip_contacts=["alice@example.com"],
        app_url="https://app.example.com",
        classify=_no_urgent_language,
    )

    assert action is not None
    assert action.type == ActionType.SEND_EMAIL
    assert action.payload["to"] == "me@example.com"
    assert action.payload["kind"] == "urgent_notification"
    assert "Alice Boss" in action.payload["body"] or "alice@example.com" in action.payload["body"]
    assert "https://app.example.com" in action.payload["body"]

    # Still just a PendingAction awaiting approval — never executed.
    pending = approval.list_pending(session, owner_id="owner-1")
    assert len(pending) == 1
    assert pending[0].id == action.id


def test_maybe_propose_notification_returns_none_when_nothing_is_urgent(session):
    action = urgency.maybe_propose_notification(
        session,
        owner_id="owner-1",
        messages=[_message(sender="rando@example.com")],
        threads=[],
        owner_email="me@example.com",
        vip_contacts=["alice@example.com"],
        app_url="https://app.example.com",
        classify=_no_urgent_language,
    )

    assert action is None
    assert approval.list_pending(session, owner_id="owner-1") == []


def test_maybe_propose_notification_does_not_duplicate_within_the_dedup_window(session):
    kwargs = dict(
        owner_id="owner-1",
        messages=[_message(sender="Alice Boss <alice@example.com>")],
        threads=[],
        owner_email="me@example.com",
        vip_contacts=["alice@example.com"],
        app_url="https://app.example.com",
        classify=_no_urgent_language,
    )

    first = urgency.maybe_propose_notification(session, **kwargs)
    second = urgency.maybe_propose_notification(session, **kwargs)

    assert first is not None
    assert second is None
    assert len(approval.list_pending(session, owner_id="owner-1")) == 1


def test_maybe_propose_notification_proposes_again_after_the_dedup_window_elapses(session):
    """approval.propose stamps created_at with the real clock (no injection point there),
    so simulate an old notification by inserting the row directly rather than via a fake
    `now` passed to maybe_propose_notification."""
    old_row = PendingActionRow(
        id="old-notification",
        owner_id="owner-1",
        type=ActionType.SEND_EMAIL,
        summary="Urgent items notification (1 item)",
        payload={
            "to": "me@example.com",
            "subject": "old",
            "body": "old",
            "kind": "urgent_notification",
        },
        status=ActionStatus.PENDING,
        created_at=datetime.now(UTC) - timedelta(hours=21),  # past the 20h dedup window
    )
    session.add(old_row)
    session.commit()

    action = urgency.maybe_propose_notification(
        session,
        owner_id="owner-1",
        messages=[_message(sender="Alice Boss <alice@example.com>")],
        threads=[],
        owner_email="me@example.com",
        vip_contacts=["alice@example.com"],
        app_url="https://app.example.com",
        classify=_no_urgent_language,
    )

    assert action is not None
    assert len(approval.list_pending(session, owner_id="owner-1")) == 2


def test_maybe_propose_notification_is_scoped_per_owner(session):
    """A dedup hit for one owner must never suppress another owner's notification."""
    shared_kwargs = dict(
        messages=[_message(sender="Alice Boss <alice@example.com>")],
        threads=[],
        owner_email="me@example.com",
        vip_contacts=["alice@example.com"],
        app_url="https://app.example.com",
        classify=_no_urgent_language,
    )

    urgency.maybe_propose_notification(session, owner_id="owner-1", **shared_kwargs)
    other = urgency.maybe_propose_notification(session, owner_id="owner-2", **shared_kwargs)

    assert other is not None
