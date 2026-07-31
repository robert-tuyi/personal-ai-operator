from pydantic import BaseModel


class UrgentItem(BaseModel):
    """One reason an item was flagged urgent. Internal to services/urgency.py — used to
    build the self-notification email body, never returned from an API route."""

    reason: str  # "vip" | "urgent_language" | "stale_thread"
    title: str
    detail: str
