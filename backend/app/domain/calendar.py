from pydantic import BaseModel


class CalendarEvent(BaseModel):
    id: str
    title: str
    start: str  # RFC3339 datetime, or a bare date (YYYY-MM-DD) for all-day events
    end: str


class CalendarView(BaseModel):
    """Today's events plus upcoming events (tomorrow through the next few days) — the two
    ranges are complementary, not overlapping (see integrations/google.py)."""

    today: list[CalendarEvent] = []
    upcoming: list[CalendarEvent] = []
