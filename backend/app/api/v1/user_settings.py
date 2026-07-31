from fastapi import APIRouter

from app.core.deps import OwnerDep, SessionDep
from app.domain.user_settings import UserSettings
from app.services.user_settings import get_user_settings, save_user_settings

router = APIRouter()


@router.get("/user-settings", response_model=UserSettings)
def read_user_settings(session: SessionDep, owner_id: OwnerDep) -> UserSettings:
    return get_user_settings(session, owner_id=owner_id)


@router.put("/user-settings", response_model=UserSettings)
def update_user_settings(
    settings: UserSettings, session: SessionDep, owner_id: OwnerDep
) -> UserSettings:
    return save_user_settings(session, owner_id=owner_id, settings=settings)
