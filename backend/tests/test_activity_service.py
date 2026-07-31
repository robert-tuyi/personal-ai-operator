"""Activity log service tests — enrichment from the audit trail, owner scoping, ordering."""

import pytest

from app.core import approval
from app.domain.actions import ActionType
from app.services.activity import list_activity


@pytest.fixture(autouse=True)
def _spy_executor():
    calls: list[dict] = []
    approval.register_executor(ActionType.SEND_EMAIL, lambda payload, _ctx: calls.append(payload))
    yield calls
    approval._executors.pop(ActionType.SEND_EMAIL, None)


def _propose(session, summary="Send reply: Re: hello"):
    return approval.propose(
        session,
        owner_id="owner",
        type=ActionType.SEND_EMAIL,
        summary=summary,
        payload={"to": "a@example.com", "body": "hi"},
    )


def test_list_activity_enriches_with_action_context(session):
    action = _propose(session)
    approval.approve(session, owner_id="owner", action_id=action.id)
    approval.execute_approved(session, owner_id="owner", action_id=action.id)

    entries = list_activity(session, owner_id="owner")

    assert [e.event for e in entries] == ["executed", "approved", "proposed"]
    assert all(e.summary == "Send reply: Re: hello" for e in entries)
    assert all(e.action_type == ActionType.SEND_EMAIL for e in entries)


def test_list_activity_is_owner_scoped(session):
    _propose(session, summary="For owner")
    approval.propose(
        session,
        owner_id="someone-else",
        type=ActionType.SEND_EMAIL,
        summary="For someone else",
        payload={"to": "b@example.com", "body": "hi"},
    )

    entries = list_activity(session, owner_id="owner")
    assert [e.summary for e in entries] == ["For owner"]


def test_list_activity_empty_when_no_actions(session):
    assert list_activity(session, owner_id="owner") == []
