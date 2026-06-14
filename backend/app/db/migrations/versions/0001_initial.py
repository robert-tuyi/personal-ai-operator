"""initial: pending_action + audit_entry

Revision ID: 0001
Revises:
Create Date: 2026-06-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_action",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pending_action_owner_id", "pending_action", ["owner_id"])
    op.create_index("ix_pending_action_status", "pending_action", ["status"])

    op.create_table(
        "audit_entry",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("action_id", sa.String(), nullable=True),
        sa.Column("detail", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_entry_owner_id", "audit_entry", ["owner_id"])
    op.create_index("ix_audit_entry_action_id", "audit_entry", ["action_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_entry_action_id", table_name="audit_entry")
    op.drop_index("ix_audit_entry_owner_id", table_name="audit_entry")
    op.drop_table("audit_entry")
    op.drop_index("ix_pending_action_status", table_name="pending_action")
    op.drop_index("ix_pending_action_owner_id", table_name="pending_action")
    op.drop_table("pending_action")
