"""FastAPI dependencies shared across routes.

Identity is session-based: "Log in with Google" stores the Google account's stable subject
id ("sub") in a signed session cookie, and that id IS the owner_id threaded through the app.
Single-tenant today (ADR 0003), but nothing here hardcodes a user, so adding more is an
extension, not a rewrite — rows are already owner-scoped.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import Session

from app.db.session import get_session

# Session cookie keys written by the auth callback (api/v1/auth.py).
SESSION_OWNER_KEY = "owner_id"
SESSION_EMAIL_KEY = "email"


def current_owner_id(request: Request) -> str:
    """The logged-in owner's id, from the signed session cookie.

    401 if there is no authenticated session — the caller must log in with Google.
    """
    owner_id = request.session.get(SESSION_OWNER_KEY)
    if not owner_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not authenticated; log in with Google",
        )
    return owner_id


# Annotated dependency aliases — the current FastAPI idiom; keeps route signatures clean.
SessionDep = Annotated[Session, Depends(get_session)]
OwnerDep = Annotated[str, Depends(current_owner_id)]
