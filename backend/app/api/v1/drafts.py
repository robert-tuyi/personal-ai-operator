from fastapi import APIRouter

from app.core import approval
from app.core.deps import OwnerDep, SessionDep
from app.domain.actions import ActionType, PendingAction
from app.domain.drafts import DraftReply, IncomingMessage
from app.services.drafts import draft_reply

router = APIRouter()


@router.post("/drafts", response_model=DraftReply)
def create_draft(message: IncomingMessage, owner_id: OwnerDep) -> DraftReply:
    """Generate a reply draft. Does not send anything."""
    return draft_reply(message)


@router.post("/drafts/send", response_model=PendingAction)
def queue_send(draft: DraftReply, session: SessionDep, owner_id: OwnerDep) -> PendingAction:
    """Queue a draft for sending. Creates a PENDING action — the user must approve it
    before anything is sent."""
    return approval.propose(
        session,
        owner_id=owner_id,
        type=ActionType.SEND_EMAIL,
        summary=f"Send reply: {draft.subject}",
        payload=draft.model_dump(),
    )
