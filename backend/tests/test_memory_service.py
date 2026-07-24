"""services/memory.py tests. The embedder and (for retrieval) the search step are
injected, so nothing here hits OpenAI or requires a live Postgres/pgvector connection —
the real pgvector query in _similarity_search is exercised by running the app, not pytest
(see the module docstring in services/memory.py)."""

from datetime import UTC, datetime

from app.db.models import MemoryItemRow
from app.services import memory


def test_write_memory_persists_row_with_injected_embedding(session):
    def fake_embed(text: str) -> list[float]:
        return [1.0, 2.0, 3.0]

    item = memory.write_memory(
        session,
        owner_id="owner-1",
        content="Sounds good, see you then.",
        source="sent_email",
        embed=fake_embed,
    )

    assert item.content == "Sounds good, see you then."
    assert item.source == "sent_email"

    row = session.get(MemoryItemRow, item.id)
    assert row is not None
    assert row.owner_id == "owner-1"
    assert row.embedding == [1.0, 2.0, 3.0]


def test_retrieve_relevant_uses_injected_embed_and_search(session):
    seen: dict = {}

    def fake_embed(text: str) -> list[float]:
        seen["query"] = text
        return [9.0, 9.0]

    def fake_search(sess, owner_id, query_embedding, top_k):
        seen["owner_id"] = owner_id
        seen["query_embedding"] = query_embedding
        seen["top_k"] = top_k
        return [
            MemoryItemRow(
                id="m1",
                owner_id=owner_id,
                content="Thanks, works for me.",
                source="sent_email",
                embedding=[0.0, 0.0],
                created_at=datetime.now(UTC),
            )
        ]

    results = memory.retrieve_relevant(
        session,
        owner_id="owner-1",
        query="Can we move the call?",
        top_k=2,
        embed=fake_embed,
        search=fake_search,
    )

    assert seen["query"] == "Can we move the call?"
    assert seen["owner_id"] == "owner-1"
    assert seen["query_embedding"] == [9.0, 9.0]
    assert seen["top_k"] == 2
    assert len(results) == 1
    assert results[0].content == "Thanks, works for me."


def test_retrieve_relevant_returns_empty_when_no_memories(session):
    def fake_embed(text: str) -> list[float]:
        return [0.0]

    def fake_search(sess, owner_id, query_embedding, top_k):
        return []

    results = memory.retrieve_relevant(
        session, owner_id="owner-1", query="anything", embed=fake_embed, search=fake_search
    )

    assert results == []
