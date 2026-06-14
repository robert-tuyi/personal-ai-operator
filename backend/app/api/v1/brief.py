from fastapi import APIRouter

from app.core.deps import OwnerDep, SessionDep
from app.domain.brief import DailyBrief
from app.integrations import google
from app.services.brief import build_daily_brief

router = APIRouter()


@router.get("/brief", response_model=DailyBrief)
def get_brief(session: SessionDep, owner_id: OwnerDep) -> DailyBrief:
    messages = google.list_recent_messages(session, owner_id=owner_id)
    events = google.todays_events(session, owner_id=owner_id)
    return build_daily_brief(messages, events)
