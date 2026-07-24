"""Follow-up engine (Phase 3, mvp-scope.md "Follow-up suggestions"): find sent threads the
owner is still waiting on a reply for, and draft a nudge for each.

Pure logic — Gmail thread data and the owner's own email are passed in, "now" and the nudge
generator are injected, so this is testable without network (mirrors services/brief.py's
injected summarizer).
"""

from collections.abc import Callable
from datetime import UTC, datetime

from app.domain.drafts import DraftReply
from app.domain.followups import FollowUpSuggestion
from app.integrations import llm

NowFn = Callable[[], datetime]
Generator = Callable[[str], str]


def find_stale_threads(
    threads: list[dict],
    *,
    owner_email: str,
    stale_after_days: int,
    now: NowFn | None = None,
) -> list[dict]:
    """Threads whose last message was sent by the owner and has gone unanswered for at
    least stale_after_days."""
    now = now or (lambda: datetime.now(UTC))
    current = now()

    stale: list[dict] = []
    for thread in threads:
        if owner_email.lower() not in thread["last_from"].lower():
            continue  # last message was a reply from them, not us waiting
        days_waiting = (current - thread["last_sent_at"]).days
        if days_waiting >= stale_after_days:
            stale.append({**thread, "days_waiting": days_waiting})
    return stale


def draft_followup(thread: dict, *, generate: Generator | None = None) -> DraftReply:
    """Draft a short, polite nudge for a thread that's gone quiet."""
    generate = generate or (lambda prompt: llm.complete(prompt, quality=True))

    prompt = (
        "Draft a short, polite follow-up nudge in the user's voice, checking in on a "
        f"message they sent {thread['days_waiting']} days ago that hasn't been answered.\n"
        f"Subject: {thread['subject']}\n"
    )
    body = generate(prompt)
    subject = (
        thread["subject"] if thread["subject"].startswith("Re:") else f"Re: {thread['subject']}"
    )
    return DraftReply(
        message_id=thread["thread_id"], to=thread["last_to"], subject=subject, body=body
    )


def build_followup_suggestions(
    threads: list[dict],
    *,
    owner_email: str,
    stale_after_days: int,
    now: NowFn | None = None,
    generate: Generator | None = None,
) -> list[FollowUpSuggestion]:
    """Bounded by the caller-supplied `threads` (see integrations.google.list_sent_threads'
    own limit) — an LLM draft is only generated for threads that actually qualify as stale,
    not the whole sent history (cost discipline)."""
    stale = find_stale_threads(
        threads, owner_email=owner_email, stale_after_days=stale_after_days, now=now
    )
    return [
        FollowUpSuggestion(
            thread_id=t["thread_id"],
            subject=t["subject"],
            to=t["last_to"],
            last_sent_at=t["last_sent_at"],
            days_waiting=t["days_waiting"],
            draft=draft_followup(t, generate=generate),
        )
        for t in stale
    ]
