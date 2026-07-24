"""LLM provider routing tests — both SDKs mocked, never hits a live API.

We patch the lazily-imported `anthropic.Anthropic` / `openai.OpenAI` clients and assert:
(a) routing follows settings.llm_provider, (b) the quality flag selects the quality model,
(c) text is extracted from each provider's distinct response shape.
"""

import sys
import types

import pytest

from app.integrations import llm


# --- fake Anthropic SDK ------------------------------------------------------
class _FakeTextBlock:
    type = "text"

    def __init__(self, text: str):
        self.text = text


class _FakeAnthropicResponse:
    def __init__(self, model: str):
        # content mixes a non-text block to prove the type filter works.
        self.content = [
            types.SimpleNamespace(type="thinking"),
            _FakeTextBlock(f"anthropic:{model}"),
        ]


class _FakeAnthropicMessages:
    def __init__(self, calls):
        self._calls = calls

    def create(self, *, model, max_tokens, messages):
        self._calls.append({"provider": "anthropic", "model": model})
        return _FakeAnthropicResponse(model)


class _FakeAnthropic:
    calls: list = []

    def __init__(self, *, api_key):
        self.messages = _FakeAnthropicMessages(_FakeAnthropic.calls)


# --- fake OpenAI SDK ---------------------------------------------------------
class _FakeOpenAIResponse:
    def __init__(self, model: str):
        msg = types.SimpleNamespace(content=f"openai:{model}")
        self.choices = [types.SimpleNamespace(message=msg)]


class _FakeOpenAICompletions:
    def __init__(self, calls):
        self._calls = calls

    def create(self, *, model, max_tokens, messages):
        self._calls.append({"provider": "openai", "model": model})
        return _FakeOpenAIResponse(model)


class _FakeEmbeddingData:
    def __init__(self, embedding: list[float]):
        self.embedding = embedding


class _FakeEmbeddingResponse:
    def __init__(self, embedding: list[float]):
        self.data = [_FakeEmbeddingData(embedding)]


class _FakeOpenAIEmbeddings:
    def __init__(self, calls):
        self._calls = calls

    def create(self, *, model, input):
        self._calls.append({"model": model, "input": input})
        return _FakeEmbeddingResponse([0.1, 0.2, 0.3])


class _FakeOpenAI:
    calls: list = []
    embedding_calls: list = []

    def __init__(self, *, api_key):
        self.chat = types.SimpleNamespace(completions=_FakeOpenAICompletions(_FakeOpenAI.calls))
        self.embeddings = _FakeOpenAIEmbeddings(_FakeOpenAI.embedding_calls)


@pytest.fixture(autouse=True)
def _mock_sdks(monkeypatch):
    """Install fake `anthropic` and `openai` modules so the lazy imports resolve to them."""
    _FakeAnthropic.calls = []
    _FakeOpenAI.calls = []
    _FakeOpenAI.embedding_calls = []
    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=_FakeAnthropic))
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=_FakeOpenAI))
    # Known model IDs so assertions don't depend on the real defaults.
    monkeypatch.setattr(llm.settings, "model_cheap", "anth-cheap")
    monkeypatch.setattr(llm.settings, "model_quality", "anth-quality")
    monkeypatch.setattr(llm.settings, "openai_model_cheap", "oai-cheap")
    monkeypatch.setattr(llm.settings, "openai_model_quality", "oai-quality")
    monkeypatch.setattr(llm.settings, "openai_embedding_model", "oai-embed")


def test_routes_to_anthropic_by_default(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "anthropic")
    out = llm.complete("hi")
    assert out == "anthropic:anth-cheap"
    assert _FakeAnthropic.calls and not _FakeOpenAI.calls


def test_routes_to_openai_when_configured(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "openai")
    out = llm.complete("hi")
    assert out == "openai:oai-cheap"
    assert _FakeOpenAI.calls and not _FakeAnthropic.calls


def test_quality_flag_selects_quality_model_anthropic(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "anthropic")
    out = llm.complete("hi", quality=True)
    assert out == "anthropic:anth-quality"
    assert _FakeAnthropic.calls[0]["model"] == "anth-quality"


def test_quality_flag_selects_quality_model_openai(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "openai")
    out = llm.complete("hi", quality=True)
    assert out == "openai:oai-quality"
    assert _FakeOpenAI.calls[0]["model"] == "oai-quality"


def test_summarize_is_cheap_anthropic(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "anthropic")
    assert llm.summarize("hi") == "anthropic:anth-cheap"


def test_summarize_is_cheap_openai(monkeypatch):
    monkeypatch.setattr(llm.settings, "llm_provider", "openai")
    assert llm.summarize("hi") == "openai:oai-cheap"


def test_anthropic_extracts_only_text_blocks(monkeypatch):
    """Non-text content blocks must be dropped from the returned string."""
    monkeypatch.setattr(llm.settings, "llm_provider", "anthropic")
    out = llm.complete("hi")
    assert out == "anthropic:anth-cheap"  # 'thinking' block excluded, only text kept


def test_openai_handles_null_content(monkeypatch):
    """A None message content coerces to empty string, not a crash."""
    monkeypatch.setattr(llm.settings, "llm_provider", "openai")

    class _NullCompletions:
        def create(self, **kwargs):
            msg = types.SimpleNamespace(content=None)
            return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    class _NullClient:
        def __init__(self, *, api_key):
            self.chat = types.SimpleNamespace(completions=_NullCompletions())

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=_NullClient))
    assert llm.complete("hi") == ""


def test_embed_always_uses_openai_even_when_provider_is_anthropic(monkeypatch):
    """Anthropic has no embeddings API — embed() must ignore llm_provider entirely."""
    monkeypatch.setattr(llm.settings, "llm_provider", "anthropic")
    out = llm.embed("hello world")
    assert out == [0.1, 0.2, 0.3]
    assert _FakeOpenAI.embedding_calls == [{"model": "oai-embed", "input": "hello world"}]
    assert not _FakeAnthropic.calls
