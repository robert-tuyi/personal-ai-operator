from fastapi import APIRouter

from app.core import approval
from app.core.deps import OwnerDep, SessionDep
from app.domain.actions import PendingAction

router = APIRouter()


@router.get("/approvals", response_model=list[PendingAction])
def list_pending(session: SessionDep, owner_id: OwnerDep) -> list[PendingAction]:
    return approval.list_pending(session, owner_id=owner_id)


@router.post("/approvals/{action_id}/approve", response_model=PendingAction)
def approve(action_id: str, session: SessionDep, owner_id: OwnerDep) -> PendingAction:
    return approval.approve(session, owner_id=owner_id, action_id=action_id)


@router.post("/approvals/{action_id}/reject", response_model=PendingAction)
def reject(action_id: str, session: SessionDep, owner_id: OwnerDep) -> PendingAction:
    return approval.reject(session, owner_id=owner_id, action_id=action_id)


@router.post("/approvals/{action_id}/execute", response_model=PendingAction)
def execute(action_id: str, session: SessionDep, owner_id: OwnerDep) -> PendingAction:
    """Execute an approved action. Refuses anything not yet approved (returns 409)."""
    return approval.execute_approved(session, owner_id=owner_id, action_id=action_id)
