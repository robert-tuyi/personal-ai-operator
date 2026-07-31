"""Daily brief: summarize what needs attention from recent mail + today's calendar.

Pure logic, no HTTP. The summarizer is injected so this is testable without network and
swappable later.
"""

from collections.abc import Callable

from app.domain.brief import BriefItem, BriefItemKind, DailyBrief
from app.integrations import llm

Summarizer = Callable[[str], str]

# How many of each to show as actionable items — a command-center list, not the whole
# inbox (CLAUDE.md cost discipline extends to UI clarity, not just token spend).
MAX_ITEMS_PER_KIND = 10


def _build_items(messages: list[dict], events: list[dict]) -> list[BriefItem]:
    """Items come straight from the raw data, not the LLM — cheaper, and more accurate
    than an LLM paraphrase of a sender/subject it was already given verbatim."""
    items = [
        BriefItem(
            kind=BriefItemKind.EMAIL,
            title=m.get("subject") or "(no subject)",
            detail=m.get("snippet", ""),
            sender=m.get("sender", ""),
            subject=m.get("subject", ""),
            message_id=m.get("id"),
        )
        for m in messages[:MAX_ITEMS_PER_KIND]
    ]
    items += [
        BriefItem(
            kind=BriefItemKind.EVENT,
            title=e.get("title") or "(untitled)",
            detail=f"{e.get('start', '?')} – {e.get('end', '?')}",
        )
        for e in events[:MAX_ITEMS_PER_KIND]
    ]
    return items


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
        "You are the user's assistant. In 1-2 short sentences, give a high-level overview "
        "of what needs attention today — the itemized list is shown separately, so don't "
        "repeat it. Based on these items:\n\n" + "\n".join(lines)
    )
    return DailyBrief(summary=summarize(prompt), items=_build_items(messages, events))
