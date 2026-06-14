from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class PendingActionRow(SQLModel, table=True):
    __tablename__ = "pending_action"

    id: str = Field(primary_key=True)
    owner_id: str = Field(index=True)  # owner-scoped for multi-tenant later (ADR 0003)
    type: str
    summary: str
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="pending", index=True)
    created_at: datetime
    decided_at: datetime | None = None
    executed_at: datetime | None = None
    error: str | None = None


class AuditEntryRow(SQLModel, table=True):
    __tablename__ = "audit_entry"

    id: str = Field(primary_key=True)
    owner_id: str = Field(index=True)
    event: str  # proposed | approved | rejected | executed | failed
    action_id: str | None = Field(default=None, index=True)
    detail: str | None = None
    created_at: datetime
