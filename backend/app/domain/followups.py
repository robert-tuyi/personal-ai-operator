from datetime import datetime

from pydantic import BaseModel

from app.domain.drafts import DraftReply


class FollowUpSuggestion(BaseModel):
    """A sent thread the owner is still waiting on a reply for, with an auto-drafted nudge
    ready to review. Queuing `draft` for sending reuses the existing drafts/approval flow
    (POST /drafts/send) unchanged — a follow-up nudge is still just an email send, gated the
    same way as any other reply."""

    thread_id: str
    subject: str
    to: str  # who we're waiting on a reply from
    last_sent_at: datetime
    days_waiting: int
    draft: DraftReply
