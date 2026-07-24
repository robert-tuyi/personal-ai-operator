from datetime import UTC, datetime

from app.domain.drafts import IncomingMessage
from app.domain.memory import MemoryItem
from app.services.drafts import draft_reply


def _message() -> IncomingMessage:
    return IncomingMessage(
        id="m1", sender="alice@example.com", subject="Lunch?", body="Free at noon?"
    )


def test_draft_uses_injected_generator_and_prefixes_subject(session):
    seen: dict = {}

    def fake_generate(prompt: str) -> str:
        seen["prompt"] = prompt
        return "Sure, noon works."

    def no_examples(*a, **k):
        return []

    draft = draft_reply(
        _message(),
        session=session,
        owner_id="owner-1",
        generate=fake_generate,
        retrieve=no_examples,
    )

    assert draft.subject == "Re: Lunch?"
    assert draft.body == "Sure, noon works."
    assert "Free at noon?" in seen["prompt"]
    assert "Examples of how the user has written before" not in seen["prompt"]


def test_draft_includes_retrieved_style_examples_in_prompt(session):
    seen: dict = {}

    def fake_generate(prompt: str) -> str:
        seen["prompt"] = prompt
        return "body"

    def fake_retrieve(sess, *, owner_id, query, top_k=3):
        seen["owner_id"] = owner_id
        seen["query"] = query
        seen["top_k"] = top_k
        return [
            MemoryItem(
                id="mem1",
                content="Sounds great!",
                source="sent_email",
                created_at=datetime.now(UTC),
            )
        ]

    draft_reply(
        _message(),
        session=session,
        owner_id="owner-1",
        generate=fake_generate,
        retrieve=fake_retrieve,
    )

    assert seen["owner_id"] == "owner-1"
    assert "Lunch?" in seen["query"]
    assert seen["top_k"] == 3
    assert "Sounds great!" in seen["prompt"]
    assert "Examples of how the user has written before" in seen["prompt"]
