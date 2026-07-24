"""Memory layer (Phase 2, ADR 0004): write what the user actually sent, retrieve what's
relevant to inform brief/draft generation.

Pure logic wrapping DB access, no HTTP. The embedder is injected (mirrors services/brief.py's
summarizer), so writing is testable without hitting OpenAI. The similarity query itself is
Postgres/pgvector-specific and is also injected as `search`, so ranking/orchestration is
testable without a live Postgres — `_similarity_search`'s real query is exercised by running
the app (docker compose), not by pytest, the same way integrations/google.py's live request
shapes are trusted rather than unit-tested against the real Gmail API.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.db.models import MemoryItemRow
from app.domain.memory import MemoryItem
from app.integrations import llm

Embedder = Callable[[str], list[float]]
Searcher = Callable[[Session, str, list[float], int], list[MemoryItemRow]]


def _to_domain(row: MemoryItemRow) -> MemoryItem:
    return MemoryItem(id=row.id, content=row.content, source=row.source, created_at=row.created_at)


def _similarity_search(
    session: Session, owner_id: str, query_embedding: list[float], top_k: int
) -> list[MemoryItemRow]:
    statement = (
        select(MemoryItemRow)
        .where(MemoryItemRow.owner_id == owner_id)
        .order_by(MemoryItemRow.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return list(session.exec(statement))


def write_memory(
    session: Session,
    *,
    owner_id: str,
    content: str,
    source: str,
    embed: Embedder | None = None,
) -> MemoryItem:
    """Persist a memory item. Call this only after an outbound action has actually
    executed (e.g. the approval executor for a sent email) — never from a draft or
    proposal, so memory reflects what really happened."""
    embed = embed or llm.embed
    row = MemoryItemRow(
        id=uuid.uuid4().hex,
        owner_id=owner_id,
        content=content,
        source=source,
        embedding=embed(content),
        created_at=datetime.now(UTC),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _to_domain(row)


def retrieve_relevant(
    session: Session,
    *,
    owner_id: str,
    query: str,
    top_k: int = 3,
    embed: Embedder | None = None,
    search: Searcher | None = None,
) -> list[MemoryItem]:
    """Top_k memory items most relevant to `query`, ranked by embedding similarity. Bounded
    to top_k so callers never feed unranked/unbounded memory into a prompt (CLAUDE.md cost
    discipline)."""
    embed = embed or llm.embed
    search = search or _similarity_search
    rows = search(session, owner_id, embed(query), top_k)
    return [_to_domain(row) for row in rows]
