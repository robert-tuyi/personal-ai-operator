from fastapi import APIRouter

from app.domain.brief import DailyBrief
from app.integrations import google
from app.services.brief import build_daily_brief

router = APIRouter()


@router.get("/brief", response_model=DailyBrief)
def get_brief() -> DailyBrief:
    messages = google.list_recent_messages()
    events = google.todays_events()
    return build_daily_brief(messages, events)
