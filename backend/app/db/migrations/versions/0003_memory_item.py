"""memory_item: stored memory fragments with embeddings (Phase 2, ADR 0004)

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-24
"""

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

EMBEDDING_DIM = 1536  # text-embedding-3-small; must match app/integrations/llm.py


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "memory_item",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(EMBEDDING_DIM), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_memory_item_owner_id", "memory_item", ["owner_id"])


def downgrade() -> None:
    op.drop_index("ix_memory_item_owner_id", table_name="memory_item")
    op.drop_table("memory_item")
    # Not dropping the vector extension — other tables may come to depend on it.
