from datetime import datetime

from pydantic import BaseModel

from app.domain.actions import ActionType


class ActivityEntry(BaseModel):
    """A single event from the approval audit log (core/audit.py), enriched with the
    related action's type and summary for display.

    This is honestly scoped to what the app actually tracks today: the outbound-action
    lifecycle (proposed/approved/rejected/executed/failed). Nothing here represents
    "read" or "classified" activity — the product doesn't instrument those yet."""

    id: str
    event: str  # proposed | approved | rejected | executed | failed
    action_type: ActionType
    summary: str
    detail: str | None = None
    created_at: datetime
