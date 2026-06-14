from app.services.brief import build_daily_brief


def test_empty_inputs_return_placeholder_without_calling_model():
    def explode(_prompt: str) -> str:  # must not be called
        raise AssertionError("summarizer should not run for empty inputs")

    brief = build_daily_brief([], [], summarize=explode)
    assert "connect" in brief.summary.lower()


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
