from fastapi import APIRouter

from app.config import get_settings
from app.core.deps import OwnerDep, SessionDep
from app.domain.followups import FollowUpSuggestion
from app.integrations import google
from app.services import oauth_tokens
from app.services.followups import build_followup_suggestions

router = APIRouter()


@router.get("/followups", response_model=list[FollowUpSuggestion])
def list_followups(session: SessionDep, owner_id: OwnerDep) -> list[FollowUpSuggestion]:
    """Sent threads still awaiting a reply, each with an auto-drafted nudge. Drafting is
    not an outbound action — queuing the nudge for sending goes through the existing
    POST /drafts/send + approval flow, same as any other reply."""
    settings = get_settings()
    token_row = oauth_tokens.get_token(session, owner_id=owner_id)
    owner_email = token_row.email if token_row else ""

    threads = google.list_sent_threads(session, owner_id=owner_id)
    return build_followup_suggestions(
        threads,
        owner_email=owner_email,
        stale_after_days=settings.followup_stale_after_days,
    )
