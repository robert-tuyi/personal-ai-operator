"""Google OAuth client (Authlib) and credential resolution.

This module owns the "Log in with Google" flow — which is also the Gmail/Calendar grant
(ADR 0003). The auth route drives the redirect/callback dance; the rest of the app calls
`access_token_for` to get a fresh access token for the stored owner, refreshing it via the
refresh token when it has expired.

No write APIs live here — sending mail / creating events still goes through the approval
chokepoint and `integrations/google.py`.
"""

import time
from functools import lru_cache

import httpx
from authlib.integrations.starlette_client import OAuth
from sqlmodel import Session

from app.config import get_settings
from app.services import oauth_tokens

# Google's OpenID discovery doc — lets Authlib resolve authorize/token/jwks endpoints.
GOOGLE_CONF_URL = "https://accounts.google.com/.well-known/openid-configuration"
TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleAuthError(Exception):
    """OAuth could not produce a usable access token (no token stored, refresh failed)."""


@lru_cache
def get_oauth() -> OAuth:
    """Build the Authlib OAuth registry with the Google client registered.

    Cached so the app shares one registry. access_type=offline + prompt=consent ensures
    Google issues a refresh token on first login.
    """
    settings = get_settings()
    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url=GOOGLE_CONF_URL,
        client_kwargs={
            "scope": settings.google_oauth_scopes,
            "access_type": "offline",
            "prompt": "consent",
        },
    )
    return oauth


def _refresh_token(refresh_token: str) -> dict:
    """Exchange a refresh token for a fresh access token (Google token endpoint)."""
    settings = get_settings()
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    token = resp.json()
    # Google's refresh response omits refresh_token; preserve the caller's one upstream.
    if "expires_in" in token and "expires_at" not in token:
        token["expires_at"] = int(time.time()) + int(token["expires_in"])
    return token


def access_token_for(session: Session, *, owner_id: str) -> str:
    """Return a valid access token for the owner, refreshing it if it has expired.

    Raises GoogleAuthError if there is no stored token or it cannot be refreshed — callers
    should treat that as "not connected / needs to log in again".
    """
    row = oauth_tokens.get_token(session, owner_id=owner_id)
    if row is None:
        raise GoogleAuthError("no Google token stored for owner; log in with Google first")

    if not oauth_tokens.is_expired(row):
        return row.access_token

    if not row.refresh_token:
        raise GoogleAuthError("access token expired and no refresh token; re-authenticate")

    refreshed = _refresh_token(row.refresh_token)
    row = oauth_tokens.save_token(
        session,
        owner_id=owner_id,
        email=row.email,
        token=refreshed,
    )
    return row.access_token
