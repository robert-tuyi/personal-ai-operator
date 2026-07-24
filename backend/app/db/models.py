from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel

from app.integrations.llm import EMBEDDING_DIM


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


class OAuthTokenRow(SQLModel, table=True):
    """A user's stored Google OAuth token (the Gmail/Calendar grant).

    Owner-scoped like everything else (ADR 0003): one row per owner today, but rows carry
    an owner_id so multi-tenant is an extension, not a rewrite. The owner_id is the Google
    account's stable subject id ("sub"), which is also what identifies the logged-in user.
    """

    __tablename__ = "oauth_token"

    owner_id: str = Field(primary_key=True)  # Google "sub" — stable per-account identifier
    email: str  # the Google account email, for display
    access_token: str
    refresh_token: str | None = None  # only issued with access_type=offline + first consent
    token_type: str = "Bearer"
    scope: str | None = None
    expires_at: datetime | None = None  # absolute UTC expiry of the access token
    created_at: datetime
    updated_at: datetime


class AuditEntryRow(SQLModel, table=True):
    __tablename__ = "audit_entry"

    id: str = Field(primary_key=True)
    owner_id: str = Field(index=True)
    event: str  # proposed | approved | rejected | executed | failed
    action_id: str | None = Field(default=None, index=True)
    detail: str | None = None
    created_at: datetime


class MemoryItemRow(SQLModel, table=True):
    """A stored fragment of the user's own past behavior, with its embedding for
    similarity search (Phase 2 memory layer, ADR 0004). Owner-scoped like everything else
    (ADR 0003)."""

    __tablename__ = "memory_item"

    id: str = Field(primary_key=True)
    owner_id: str = Field(index=True)
    content: str
    source: str  # what produced this memory, e.g. "sent_email"
    embedding: list[float] = Field(sa_column=Column(Vector(EMBEDDING_DIM), nullable=False))
    created_at: datetime
