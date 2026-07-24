"""LLM access — OpenAI (default) or Anthropic, switchable via settings.llm_provider.

Default to the cheap model; use the quality model only where output is the point
(CLAUDE.md cost discipline). Model IDs live in config; consult the claude-api reference
before changing Anthropic model behavior. Each provider's SDK is imported lazily inside
its branch, so the app boots with only the configured provider installed.
"""

from app.config import get_settings

settings = get_settings()

# Dimension of settings.openai_embedding_model's output (text-embedding-3-small = 1536).
# The memory_item table's vector column is fixed to this size (see db/models.py); changing
# the embedding model requires a migration to match.
EMBEDDING_DIM = 1536


def _complete_anthropic(prompt: str, *, quality: bool, max_tokens: int) -> str:
    from anthropic import Anthropic

    model = settings.model_quality if quality else settings.model_cheap
    response = Anthropic(api_key=settings.anthropic_api_key).messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


def _complete_openai(prompt: str, *, quality: bool, max_tokens: int) -> str:
    from openai import OpenAI

    model = settings.openai_model_quality if quality else settings.openai_model_cheap
    response = OpenAI(api_key=settings.openai_api_key).chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content or ""


def complete(prompt: str, *, quality: bool = False, max_tokens: int = 1024) -> str:
    if settings.llm_provider == "openai":
        return _complete_openai(prompt, quality=quality, max_tokens=max_tokens)
    return _complete_anthropic(prompt, quality=quality, max_tokens=max_tokens)


def summarize(prompt: str) -> str:
    return complete(prompt, quality=False)


def embed(text: str) -> list[float]:
    """Embed text for memory storage/retrieval. Always OpenAI — Anthropic has no
    embeddings API, so this ignores settings.llm_provider."""
    from openai import OpenAI

    response = OpenAI(api_key=settings.openai_api_key).embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )
    return response.data[0].embedding
