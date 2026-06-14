"""Draft a reply in the user's style. Drafting only — sending goes through approval.

The generator is injected so this is testable without network.
"""

from collections.abc import Callable

from app.domain.drafts import DraftReply, IncomingMessage
from app.integrations import llm

Generator = Callable[[str], str]


def draft_reply(message: IncomingMessage, *, generate: Generator | None = None) -> DraftReply:
    generate = generate or (lambda prompt: llm.complete(prompt, quality=True))

    prompt = (
        "Draft a reply in the user's voice — natural, concise, matching their tone.\n"
        f"From: {message.sender}\n"
        f"Subject: {message.subject}\n\n"
        f"{message.body}"
    )
    body = generate(prompt)
    subject = message.subject if message.subject.startswith("Re:") else f"Re: {message.subject}"
    return DraftReply(message_id=message.id, subject=subject, body=body)
