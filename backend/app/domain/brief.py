from enum import StrEnum

from pydantic import BaseModel


class BriefItemKind(StrEnum):
    EMAIL = "email"
    EVENT = "event"


class BriefItem(BaseModel):
    """One actionable thing in the brief — built directly from the raw Gmail/Calendar
    data, not from the LLM (cheaper, and more accurate than an LLM paraphrase). sender/
    subject/message_id are only set for kind=email; they let the frontend deep-link a
    "Compose reply" action straight to that message."""

    kind: BriefItemKind
    title: str
    detail: str
    sender: str | None = None
    subject: str | None = None
    message_id: str | None = None


class DailyBrief(BaseModel):
    summary: str
    items: list[BriefItem] = []
