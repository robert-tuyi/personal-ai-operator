from app.domain.brief import BriefItemKind
from app.services.brief import build_daily_brief


def test_empty_inputs_return_placeholder_without_calling_model():
    def explode(_prompt: str) -> str:  # must not be called
        raise AssertionError("summarizer should not run for empty inputs")

    brief = build_daily_brief([], [], summarize=explode)
    assert "connect" in brief.summary.lower()
    assert brief.items == []


def test_brief_uses_injected_summarizer_with_bounded_input():
    seen: dict[str, str] = {}

    def fake_summarize(prompt: str) -> str:
        seen["prompt"] = prompt
        return "Two things need attention."

    messages = [{"sender": "boss@x.com", "subject": "Q3 plan"}]
    events = [{"start": "10:00", "title": "Standup"}]
    brief = build_daily_brief(messages, events, summarize=fake_summarize)

    assert brief.summary == "Two things need attention."
    assert "Q3 plan" in seen["prompt"]
    assert "Standup" in seen["prompt"]


def test_items_are_built_from_raw_data_not_the_model():
    """Items must not depend on the LLM at all — they come straight from the inputs,
    so a summarizer that ignores its prompt still produces correct, actionable items."""
    messages = [
        {"id": "m1", "sender": "boss@x.com", "subject": "Q3 plan", "snippet": "See attached."}
    ]
    events = [{"id": "e1", "title": "Standup", "start": "10:00", "end": "10:15"}]
    brief = build_daily_brief(messages, events, summarize=lambda _p: "ignored")

    assert len(brief.items) == 2
    email_item, event_item = brief.items

    assert email_item.kind == BriefItemKind.EMAIL
    assert email_item.title == "Q3 plan"
    assert email_item.detail == "See attached."
    assert email_item.sender == "boss@x.com"
    assert email_item.subject == "Q3 plan"
    assert email_item.message_id == "m1"

    assert event_item.kind == BriefItemKind.EVENT
    assert event_item.title == "Standup"
    assert event_item.detail == "10:00 – 10:15"
    assert event_item.sender is None


def test_items_are_bounded_per_kind():
    messages = [{"id": str(i), "sender": "a@x.com", "subject": f"m{i}"} for i in range(15)]
    brief = build_daily_brief(messages, [], summarize=lambda _p: "ok")
    assert len(brief.items) == 10


def test_missing_subject_and_snippet_fall_back_gracefully():
    messages = [{"id": "m1", "sender": "a@x.com"}]
    brief = build_daily_brief(messages, [], summarize=lambda _p: "ok")
    assert brief.items[0].title == "(no subject)"
    assert brief.items[0].detail == ""
