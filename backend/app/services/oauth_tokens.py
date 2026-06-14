"""Persistence for Google OAuth tokens.

Plain functions over a SQLModel session (no HTTP), so they're testable in isolation. The
table is owner-scoped (ADR 0003): the owner_id is the Google account's stable subject id.

A token dict here matches Authlib's token shape: access_token, refresh_token, token_type,
scope, and either expires_at (absolute epoch seconds) or expires_in (relative seconds).
"""

from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app.db.models import OAuthTokenRow


def _now() -> datetime:
    return datetime.now(UTC)


def _expires_at(token: dict) -> datetime | None:
    """Resolve an absolute UTC expiry from Authlib's token shape."""
    if token.get("expires_at") is not None:
        return datetime.fromtimestamp(int(token["expires_at"]), tz=UTC)
    if token.get("expires_in") is not None:
        return _now() + timedelta(seconds=int(token["expires_in"]))
    return None


def save_token(
    session: Session,
    *,
    owner_id: str,
    email: str,
    token: dict,
) -> OAuthTokenRow:
    """Upsert the stored token for an owner.

    Refresh tokens are only issued by Google on the first consent; a re-auth or refresh may
    return a token without one. Never clobber a stored refresh_token with None.
    """
    now = _now()
    row = session.get(OAuthTokenRow, owner_id)
    new_refresh = token.get("refresh_token")

    if row is None:
        row = OAuthTokenRow(
            owner_id=owner_id,
            email=email,
            access_token=token["access_token"],
            refresh_token=new_refresh,
            token_type=token.get("token_type", "Bearer"),
            scope=token.get("scope"),
            expires_at=_expires_at(token),
            created_at=now,
            updated_at=now,
        )
    else:
        row.email = email
        row.access_token = token["access_token"]
        if new_refresh:  # keep the existing refresh token if the new payload omits one
            row.refresh_token = new_refresh
        row.token_type = token.get("token_type", row.token_type)
        if token.get("scope"):
            row.scope = token["scope"]
        row.expires_at = _expires_at(token)
        row.updated_at = now

    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_token(session: Session, *, owner_id: str) -> OAuthTokenRow | None:
    return session.get(OAuthTokenRow, owner_id)


def is_expired(row: OAuthTokenRow, *, skew_seconds: int = 60) -> bool:
    """True if the access token is expired (or within skew of expiring)."""
    if row.expires_at is None:
        return False
    expires_at = row.expires_at
    if expires_at.tzinfo is None:  # SQLite round-trips naive datetimes
        expires_at = expires_at.replace(tzinfo=UTC)
    return _now() >= expires_at - timedelta(seconds=skew_seconds)
