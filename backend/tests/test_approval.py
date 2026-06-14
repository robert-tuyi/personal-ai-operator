"""Tests for the approval chokepoint — these guard invariant #1.

The negative path (refusing to execute an unapproved action) is the most important test
in the codebase. Do not weaken it.
"""

import pytest

from app.core import approval, audit
from app.domain.actions import ActionStatus, ActionType


@pytest.fixture(autouse=True)
def _spy_executor():
    """Register a spy executor for SEND_EMAIL and clean up the global registry after."""
    calls: list[dict] = []
    approval.register_executor(ActionType.SEND_EMAIL, calls.append)
    yield calls
    approval._executors.pop(ActionType.SEND_EMAIL, None)


def _propose(session):
    return approval.propose(
        session,
        owner_id="owner",
        type=ActionType.SEND_EMAIL,
        summary="Send reply: Re: hello",
        payload={"to": "a@example.com", "body": "hi"},
    )


def test_propose_creates_pending_and_audits(session):
    action = _propose(session)
    assert action.status == ActionStatus.PENDING
    events = [e.event for e in audit.list_entries(session, owner_id="owner")]
    assert events == ["proposed"]


def test_execute_refuses_without_approval(session, _spy_executor):
    """INVARIANT: a pending (unapproved) action must never run."""
    action = _propose(session)

    with pytest.raises(approval.ApprovalError):
        approval.execute_approved(session, owner_id="owner", action_id=action.id)

    # The side effect must not have happened.
    assert _spy_executor == []


def test_full_flow_propose_approve_execute(session, _spy_executor):
    action = _propose(session)
    approval.approve(session, owner_id="owner", action_id=action.id)
    executed = approval.execute_approved(session, owner_id="owner", action_id=action.id)

    assert executed.status == ActionStatus.EXECUTED
    assert len(_spy_executor) == 1  # executor ran exactly once
    events = [e.event for e in audit.list_entries(session, owner_id="owner")]
    assert events == ["proposed", "approved", "executed"]


def test_reject_blocks_execution(session, _spy_executor):
    action = _propose(session)
    approval.reject(session, owner_id="owner", action_id=action.id)

    with pytest.raises(approval.ApprovalError):
        approval.execute_approved(session, owner_id="owner", action_id=action.id)
    assert _spy_executor == []


def test_cannot_approve_someone_elses_action(session):
    action = _propose(session)
    with pytest.raises(approval.ApprovalError):
        approval.approve(session, owner_id="intruder", action_id=action.id)
