"""Activity log: the approval audit trail (core/audit.py), enriched with each event's
related action for display. No HTTP, no new event types — every audit entry is already
tied to a PendingActionRow (see core/approval.py, which always passes action_id)."""

from sqlmodel import Session, select

from app.core import audit
from app.db.models import PendingActionRow
from app.domain.actions import ActionType
from app.domain.activity import ActivityEntry


def list_activity(session: Session, *, owner_id: str) -> list[ActivityEntry]:
    """All audit entries for an owner, newest first, with action context attached."""
    entries = audit.list_entries(session, owner_id=owner_id)

    action_ids = {e.action_id for e in entries if e.action_id}
    actions: dict[str, PendingActionRow] = {}
    if action_ids:
        rows = session.exec(
            select(PendingActionRow).where(PendingActionRow.id.in_(action_ids))
        )
        actions = {row.id: row for row in rows}

    result = [
        ActivityEntry(
            id=e.id,
            event=e.event,
            action_type=ActionType(action.type),
            summary=action.summary,
            detail=e.detail,
            created_at=e.created_at,
        )
        for e in entries
        if (action := actions.get(e.action_id))
    ]
    return sorted(result, key=lambda e: e.created_at, reverse=True)
