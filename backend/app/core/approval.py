"""The approval chokepoint — the single place outbound actions pass through.

INVARIANT (CLAUDE.md #1): nothing sends email or changes a calendar except by executing
an APPROVED action here. Services never call Gmail/Calendar write APIs directly; they
`propose()` an action, the user approves it, and only then does `execute_approved()` run
the registered executor. Do not add bypasses.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.core import audit
from app.db.models import PendingActionRow
from app.domain.actions import ActionStatus, ActionType, PendingAction


class ApprovalError(Exception):
    """An action was acted on outside its allowed lifecycle (e.g. executed unapproved)."""


# Executors actually perform the side effect for a given action type. They are registered
# by the integration that owns the side effect (see integrations/google.py) and invoked
# ONLY from execute_approved below. They receive the action payload plus a context carrying
# the owning DB session and owner_id, so the executor can resolve owner-scoped credentials
# (e.g. the Google OAuth token) at execution time without any service/route touching a
# write API directly.
ActionExecutor = Callable[[dict, "ExecutionContext"], None]
_executors: dict[ActionType, ActionExecutor] = {}


class ExecutionContext:
    """What an executor needs to perform an owner-scoped side effect."""

    def __init__(self, session: Session, owner_id: str) -> None:
        self.session = session
        self.owner_id = owner_id


def register_executor(action_type: ActionType, fn: ActionExecutor) -> None:
    _executors[action_type] = fn


def _now() -> datetime:
    return datetime.now(UTC)


def _to_domain(row: PendingActionRow) -> PendingAction:
    return PendingAction(
        id=row.id,
        type=ActionType(row.type),
        summary=row.summary,
        payload=row.payload,
        status=ActionStatus(row.status),
        created_at=row.created_at,
        decided_at=row.decided_at,
        executed_at=row.executed_at,
        error=row.error,
    )


def _get(session: Session, owner_id: str, action_id: str) -> PendingActionRow:
    row = session.get(PendingActionRow, action_id)
    if row is None or row.owner_id != owner_id:
        raise ApprovalError(f"action {action_id} not found")
    return row


def propose(
    session: Session,
    *,
    owner_id: str,
    type: ActionType,
    summary: str,
    payload: dict,
) -> PendingAction:
    """Queue an outbound action for the user to approve. Never executes anything."""
    row = PendingActionRow(
        id=uuid.uuid4().hex,
        owner_id=owner_id,
        type=type,
        summary=summary,
        payload=payload,
        status=ActionStatus.PENDING,
        created_at=_now(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    audit.record(session, owner_id=owner_id, event="proposed", action_id=row.id, detail=summary)
    return _to_domain(row)


def list_pending(session: Session, *, owner_id: str) -> list[PendingAction]:
    statement = select(PendingActionRow).where(
        PendingActionRow.owner_id == owner_id,
        PendingActionRow.status == ActionStatus.PENDING,
    )
    return [_to_domain(r) for r in session.exec(statement)]


def approve(session: Session, *, owner_id: str, action_id: str) -> PendingAction:
    row = _get(session, owner_id, action_id)
    if row.status != ActionStatus.PENDING:
        raise ApprovalError(f"cannot approve action in status {row.status}")
    row.status = ActionStatus.APPROVED
    row.decided_at = _now()
    session.add(row)
    session.commit()
    session.refresh(row)
    audit.record(session, owner_id=owner_id, event="approved", action_id=row.id)
    return _to_domain(row)


def reject(session: Session, *, owner_id: str, action_id: str) -> PendingAction:
    row = _get(session, owner_id, action_id)
    if row.status != ActionStatus.PENDING:
        raise ApprovalError(f"cannot reject action in status {row.status}")
    row.status = ActionStatus.REJECTED
    row.decided_at = _now()
    session.add(row)
    session.commit()
    session.refresh(row)
    audit.record(session, owner_id=owner_id, event="rejected", action_id=row.id)
    return _to_domain(row)


def execute_approved(session: Session, *, owner_id: str, action_id: str) -> PendingAction:
    """Run the side effect for an approved action. Refuses anything not APPROVED."""
    row = _get(session, owner_id, action_id)

    # The invariant, enforced: only an approved action may run.
    if row.status != ActionStatus.APPROVED:
        raise ApprovalError(
            f"refusing to execute action in status {row.status}; only approved actions run"
        )

    executor = _executors.get(ActionType(row.type))
    if executor is None:
        raise ApprovalError(f"no executor registered for {row.type}")

    try:
        executor(row.payload, ExecutionContext(session=session, owner_id=owner_id))
    except Exception as exc:  # noqa: BLE001 - record the failure, then re-raise
        row.status = ActionStatus.FAILED
        row.error = str(exc)
        row.executed_at = _now()
        session.add(row)
        session.commit()
        audit.record(session, owner_id=owner_id, event="failed", action_id=row.id, detail=str(exc))
        raise

    row.status = ActionStatus.EXECUTED
    row.executed_at = _now()
    session.add(row)
    session.commit()
    session.refresh(row)
    audit.record(session, owner_id=owner_id, event="executed", action_id=row.id)
    return _to_domain(row)
