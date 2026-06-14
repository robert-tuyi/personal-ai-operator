"""Anthropic LLM access.

Default to the cheap model; use the quality model only where output is the point
(CLAUDE.md cost discipline). Model IDs live in config; consult the claude-api reference
before changing model behavior.
"""

from app.config import get_settings

settings = get_settings()


def _client():
    # Imported lazily so the app boots without the SDK configured.
    from anthropic import Anthropic

    return Anthropic(api_key=settings.anthropic_api_key)


def complete(prompt: str, *, quality: bool = False, max_tokens: int = 1024) -> str:
    model = settings.model_quality if quality else settings.model_cheap
    response = _client().messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


def summarize(prompt: str) -> str:
    return complete(prompt, quality=False)
