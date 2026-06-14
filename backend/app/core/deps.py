"""FastAPI dependencies shared across routes."""

from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from app.db.session import get_session

# Single-tenant for now (ADR 0003). The owner id is threaded through everything so that
# adding real users later is an extension, not a rewrite — don't hardcode it elsewhere.
OWNER_ID = "owner"


def current_owner_id() -> str:
    return OWNER_ID


# Annotated dependency aliases — the current FastAPI idiom; keeps route signatures clean.
SessionDep = Annotated[Session, Depends(get_session)]
OwnerDep = Annotated[str, Depends(current_owner_id)]
