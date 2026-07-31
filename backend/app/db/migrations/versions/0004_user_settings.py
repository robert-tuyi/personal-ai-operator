"""user_settings: stored per-owner preferences (work hours, timezone, tone, VIP contacts,
escalation rules, onboarding status)

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-31
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("work_hours_start", sa.String(), nullable=False),
        sa.Column("work_hours_end", sa.String(), nullable=False),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("tone", sa.String(), nullable=False),
        sa.Column("vip_contacts", sa.JSON(), nullable=False),
        sa.Column("escalation_rules", sa.JSON(), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("owner_id"),
    )


def downgrade() -> None:
    op.drop_table("user_settings")
