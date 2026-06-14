"""Daily brief: summarize what needs attention from recent mail + today's calendar.

Pure logic, no HTTP. The summarizer is injected so this is testable without network and
swappable later.
"""

from collections.abc import Callable

from app.domain.brief import DailyBrief
from app.integrations import llm

Summarizer = Callable[[str], str]


def build_daily_brief(
    messages: list[dict],
    events: list[dict],
    *,
    summarize: Summarizer | None = None,
) -> DailyBrief:
    if not messages and not events:
        return DailyBrief(summary="Nothing to brief yet — connect Gmail and Calendar.")

    summarize = summarize or llm.summarize

    # Bound what we send to the model — never dump a whole inbox (CLAUDE.md cost discipline).
    lines: list[str] = []
    for m in messages[:20]:
        lines.append(f"Email from {m.get('sender', '?')}: {m.get('subject', '(no subject)')}")
    for e in events[:20]:
        lines.append(f"Event at {e.get('start', '?')}: {e.get('title', '(untitled)')}")

    prompt = (
        "You are the user's assistant. Write a short daily brief of what needs attention, "
        "based on these items:\n\n" + "\n".join(lines)
    )
    return DailyBrief(summary=summarize(prompt))
