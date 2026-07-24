"""services/followups.py tests. Gmail thread data, "now", and the nudge generator are all
injected, so nothing here hits Gmail, an LLM, or needs a live session."""

from datetime import UTC, datetime

from app.services import followups


def _thread(**overrides) -> dict:
    base = {
        "thread_id": "t1",
        "subject": "Proposal",
        "last_from": "me@example.com",
        "last_to": "bob@example.com",
        "last_sent_at": datetime(2026, 7, 1, tzinfo=UTC),
    }
    return {**base, **overrides}


def _fixed_now(dt: datetime):
    return lambda: dt


def test_find_stale_threads_includes_owner_sent_threads_past_threshold():
    threads = [_thread()]

    stale = followups.find_stale_threads(
        threads,
        owner_email="me@example.com",
        stale_after_days=3,
        now=_fixed_now(datetime(2026, 7, 5, tzinfo=UTC)),  # 4 days later
    )

    assert len(stale) == 1
    assert stale[0]["days_waiting"] == 4


def test_find_stale_threads_excludes_threads_not_yet_stale():
    threads = [_thread()]

    stale = followups.find_stale_threads(
        threads,
        owner_email="me@example.com",
        stale_after_days=3,
        now=_fixed_now(datetime(2026, 7, 2, tzinfo=UTC)),  # 1 day later
    )

    assert stale == []


def test_find_stale_threads_excludes_threads_where_they_replied():
    """Last message from the other party means we're not the one waiting."""
    threads = [_thread(last_from="bob@example.com")]

    stale = followups.find_stale_threads(
        threads,
        owner_email="me@example.com",
        stale_after_days=3,
        now=_fixed_now(datetime(2026, 8, 1, tzinfo=UTC)),
    )

    assert stale == []


def test_draft_followup_uses_injected_generator_and_prefixes_subject():
    seen: dict = {}

    def fake_generate(prompt: str) -> str:
        seen["prompt"] = prompt
        return "Just checking in on this!"

    thread = {**_thread(), "days_waiting": 5}
    draft = followups.draft_followup(thread, generate=fake_generate)

    assert draft.subject == "Re: Proposal"
    assert draft.body == "Just checking in on this!"
    assert draft.to == "bob@example.com"
    assert "5 days ago" in seen["prompt"]


def test_build_followup_suggestions_only_drafts_for_stale_threads():
    draft_calls: list[dict] = []

    def fake_generate(prompt: str) -> str:
        draft_calls.append({"prompt": prompt})
        return "Nudge text"

    threads = [
        _thread(thread_id="stale", last_sent_at=datetime(2026, 7, 1, tzinfo=UTC)),
        _thread(thread_id="fresh", last_sent_at=datetime(2026, 7, 4, tzinfo=UTC)),
    ]

    suggestions = followups.build_followup_suggestions(
        threads,
        owner_email="me@example.com",
        stale_after_days=3,
        now=_fixed_now(datetime(2026, 7, 5, tzinfo=UTC)),
        generate=fake_generate,
    )

    assert len(suggestions) == 1
    assert suggestions[0].thread_id == "stale"
    assert suggestions[0].days_waiting == 4
    assert suggestions[0].draft.body == "Nudge text"
    assert len(draft_calls) == 1  # never drafted for the non-stale thread
