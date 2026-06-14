from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class ActionType(StrEnum):
    """Kinds of outbound action that require approval before execution."""

    SEND_EMAIL = "send_email"
    CREATE_CALENDAR_EVENT = "create_calendar_event"


class ActionStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class PendingAction(BaseModel):
    """An outbound action awaiting (or having passed through) human approval.

    Nothing in this app sends or changes anything in the outside world except by
    executing an APPROVED PendingAction via the approval chokepoint.
    """

    id: str
    type: ActionType
    summary: str  # human-readable, shown in the approval queue
    payload: dict[str, Any]  # data needed to execute (e.g. to, subject, body)
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime
    decided_at: datetime | None = None
    executed_at: datetime | None = None
    error: str | None = None
