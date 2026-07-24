"""Draft a reply in the user's style. Drafting only — sending goes through approval.

The generator and retriever are injected so this is testable without network or DB.
"""

from collections.abc import Callable

from sqlmodel import Session

from app.domain.drafts import DraftReply, IncomingMessage
from app.domain.memory import MemoryItem
from app.integrations import llm
from app.services import memory

Generator = Callable[[str], str]
Retriever = Callable[..., list[MemoryItem]]


def draft_reply(
    message: IncomingMessage,
    *,
    session: Session,
    owner_id: str,
    generate: Generator | None = None,
    retrieve: Retriever | None = None,
) -> DraftReply:
    generate = generate or (lambda prompt: llm.complete(prompt, quality=True))
    retrieve = retrieve or memory.retrieve_relevant

    # Style examples from what the user has actually sent before (Phase 2 memory layer,
    # ADR 0004) — bounded to top_k so this never balloons the prompt (cost discipline).
    examples = retrieve(
        session, owner_id=owner_id, query=f"{message.subject}\n{message.body}", top_k=3
    )
    style_block = ""
    if examples:
        joined = "\n".join(f"- {e.content}" for e in examples)
        style_block = f"Examples of how the user has written before:\n{joined}\n\n"

    prompt = (
        "Draft a reply in the user's voice — natural, concise, matching their tone.\n"
        f"{style_block}"
        f"From: {message.sender}\n"
        f"Subject: {message.subject}\n\n"
        f"{message.body}"
    )
    body = generate(prompt)
    subject = message.subject if message.subject.startswith("Re:") else f"Re: {message.subject}"
    return DraftReply(message_id=message.id, to=message.sender, subject=subject, body=body)
