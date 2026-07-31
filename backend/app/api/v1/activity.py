from fastapi import APIRouter

from app.core.deps import OwnerDep, SessionDep
from app.domain.activity import ActivityEntry
from app.services.activity import list_activity

router = APIRouter()


@router.get("/activity", response_model=list[ActivityEntry])
def read_activity(session: SessionDep, owner_id: OwnerDep) -> list[ActivityEntry]:
    return list_activity(session, owner_id=owner_id)
