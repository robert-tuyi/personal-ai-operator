from fastapi import APIRouter

from app.core.deps import OwnerDep, SessionDep
from app.domain.calendar import CalendarView
from app.integrations import google

router = APIRouter()


@router.get("/calendar", response_model=CalendarView)
def get_calendar(session: SessionDep, owner_id: OwnerDep) -> CalendarView:
    """Today's events plus upcoming events (tomorrow through the next week)."""
    return CalendarView(
        today=google.todays_events(session, owner_id=owner_id),
        upcoming=google.upcoming_events(session, owner_id=owner_id),
    )
