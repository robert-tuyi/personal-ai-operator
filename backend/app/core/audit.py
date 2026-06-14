"""Audit log. Every approval-lifecycle event is recorded here (invariant #2).

No outbound action happens without a corresponding audit trail: proposed → approved /
rejected → executed / failed.
"""

import uuid
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.db.models import AuditEntryRow


def record(
    session: Session,
    *,
    owner_id: str,
    event: str,
    action_id: str | None = None,
    detail: str | None = None,
) -> None:
    entry = AuditEntryRow(
        id=uuid.uuid4().hex,
        owner_id=owner_id,
        event=event,
        action_id=action_id,
        detail=detail,
        created_at=datetime.now(UTC),
    )
    session.add(entry)
    session.commit()


def list_entries(session: Session, *, owner_id: str) -> list[AuditEntryRow]:
    statement = (
        select(AuditEntryRow)
        .where(AuditEntryRow.owner_id == owner_id)
        .order_by(AuditEntryRow.created_at)
    )
    return list(session.exec(statement))
