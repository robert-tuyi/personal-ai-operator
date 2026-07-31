import logging

from fastapi import APIRouter
from sqlmodel import Session

from app.config import get_settings
from app.core.deps import OwnerDep, SessionDep
from app.domain.brief import DailyBrief
from app.integrations import google
from app.services import oauth_tokens, urgency, user_settings
from app.services.brief import build_daily_brief

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/brief", response_model=DailyBrief)
def get_brief(session: SessionDep, owner_id: OwnerDep) -> DailyBrief:
    messages = google.list_recent_messages(session, owner_id=owner_id)
    events = google.todays_events(session, owner_id=owner_id)
    brief = build_daily_brief(messages, events)

    # Best-effort: an urgent-notification proposal is a bonus, never a reason to fail the
    # brief the user is actively waiting on. It only ever queues a PendingAction for the
    # user to approve — see services/urgency.py.
    try:
        _maybe_propose_urgent_notification(session, owner_id=owner_id, messages=messages)
    except Exception:
        logger.exception("failed to check for urgent items; brief still returned")

    return brief


def _maybe_propose_urgent_notification(
    session: Session, *, owner_id: str, messages: list[dict]
) -> None:
    settings = get_settings()
    token_row = oauth_tokens.get_token(session, owner_id=owner_id)
    owner_email = token_row.email if token_row else ""

    threads = google.list_sent_threads(session, owner_id=owner_id)
    vip_contacts = user_settings.get_user_settings(session, owner_id=owner_id).vip_contacts

    urgency.maybe_propose_notification(
        session,
        owner_id=owner_id,
        messages=messages,
        threads=threads,
        owner_email=owner_email,
        vip_contacts=vip_contacts,
        app_url=settings.app_url,
    )
