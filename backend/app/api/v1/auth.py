"""Google OAuth login routes.

"Log in with Google" is both authentication and the Gmail/Calendar grant (ADR 0003):

    GET  /auth/login    -> redirect to Google's consent screen
    GET  /auth/callback -> Google redirects here; we exchange the code, store the token,
                           and set the session cookie identifying the user
    POST /auth/logout   -> clear the session cookie
    GET  /auth/me       -> who is logged in (or 401)

This is the ONLY place tokens are minted/stored. Write APIs still go through the approval
chokepoint — logging in never sends anything.
"""

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.config import get_settings
from app.core.deps import SESSION_EMAIL_KEY, SESSION_OWNER_KEY, SessionDep
from app.integrations.google_oauth import get_oauth
from app.services import oauth_tokens

router = APIRouter()


class AuthStatus(BaseModel):
    authenticated: bool
    owner_id: str | None = None
    email: str | None = None


@router.get("/auth/login")
async def login(request: Request) -> RedirectResponse:
    """Kick off the OAuth flow by redirecting the user to Google's consent screen."""
    settings = get_settings()
    google = get_oauth().create_client("google")
    return await google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/auth/callback")
async def callback(request: Request, session: SessionDep) -> RedirectResponse:
    """Handle Google's redirect: exchange the code for a token, persist it, set the session."""
    google = get_oauth().create_client("google")
    token = await google.authorize_access_token(request)

    # ADR 0003: don't silently treat a partial grant as full access. Per RFC 6749 §5.1, the
    # token response omits `scope` entirely when it matches what was requested — only check
    # when Google actually sent one back.
    granted_scope = token.get("scope")
    if granted_scope is not None:
        settings = get_settings()
        requested = set(settings.google_oauth_scopes.split())
        missing = requested - set(granted_scope.split())
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Google did not grant all requested permissions (missing: "
                    f"{', '.join(sorted(missing))}). Please retry and approve all "
                    "requested access."
                ),
            )

    # userinfo carries the OpenID claims (parsed by Authlib from the id_token).
    userinfo = token.get("userinfo") or {}
    sub = userinfo.get("sub")
    email = userinfo.get("email")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return a user identity",
        )

    oauth_tokens.save_token(session, owner_id=sub, email=email or "", token=token)

    # The Google "sub" is the owner_id threaded through the rest of the app.
    request.session[SESSION_OWNER_KEY] = sub
    request.session[SESSION_EMAIL_KEY] = email
    # Relative redirect → resolves to the origin the browser used (the frontend at :3000,
    # via the /api proxy), so post-login lands on the app regardless of host/port.
    return RedirectResponse(url="/brief")


@router.post("/auth/logout")
async def logout(request: Request) -> JSONResponse:
    """Clear the session cookie. Does not revoke the stored Google grant."""
    request.session.clear()
    return JSONResponse(content={"detail": "logged out"})


@router.get("/auth/me", response_model=AuthStatus)
def me(request: Request) -> AuthStatus:
    owner_id = request.session.get(SESSION_OWNER_KEY)
    if not owner_id:
        return AuthStatus(authenticated=False)
    return AuthStatus(
        authenticated=True,
        owner_id=owner_id,
        email=request.session.get(SESSION_EMAIL_KEY),
    )
