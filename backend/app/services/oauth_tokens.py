"""Persistence for Google OAuth tokens.

Plain functions over a SQLModel session (no HTTP), so they're testable in isolation. The
table is owner-scoped (ADR 0003): the owner_id is the Google account's stable subject id.

A token dict here matches Authlib's token shape: access_token, refresh_token, token_type,
scope, and either expires_at (absolute epoch seconds) or expires_in (relative seconds).
"""

from datetime import UTC, datetime, timedelta

from sqlmodel import Session

from app.core import crypto
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

    Tokens are encrypted at rest (ADR 0003, core/crypto.py) — the DB only ever holds
    ciphertext. The row returned here has plaintext access_token/refresh_token, matching
    what callers (e.g. access_token_for, which uses .access_token directly as a Bearer
    token) need; it is expunged from the session so that plaintext can't accidentally get
    flushed back to the database.

    Refresh tokens are only issued by Google on the first consent; a re-auth or refresh may
    return a token without one. Never clobber a stored refresh_token with None.
    """
    now = _now()
    row = session.get(OAuthTokenRow, owner_id)
    plaintext_access = token["access_token"]
    new_refresh = token.get("refresh_token")
    # Keep the existing refresh token (decrypted) if this payload omits one.
    if new_refresh:
        plaintext_refresh = new_refresh
    elif row is not None and row.refresh_token:
        plaintext_refresh = crypto.decrypt(row.refresh_token)
    else:
        plaintext_refresh = None

    encrypted_access = crypto.encrypt(plaintext_access)
    encrypted_refresh = crypto.encrypt(plaintext_refresh) if plaintext_refresh else None

    if row is None:
        row = OAuthTokenRow(
            owner_id=owner_id,
            email=email,
            access_token=encrypted_access,
            refresh_token=encrypted_refresh,
            token_type=token.get("token_type", "Bearer"),
            scope=token.get("scope"),
            expires_at=_expires_at(token),
            created_at=now,
            updated_at=now,
        )
    else:
        row.email = email
        row.access_token = encrypted_access
        if encrypted_refresh:
            row.refresh_token = encrypted_refresh
        row.token_type = token.get("token_type", row.token_type)
        if token.get("scope"):
            row.scope = token["scope"]
        row.expires_at = _expires_at(token)
        row.updated_at = now

    session.add(row)
    session.commit()
    session.refresh(row)  # materialize all attributes before detaching below

    row.access_token = plaintext_access
    row.refresh_token = plaintext_refresh
    session.expunge(row)
    return row


def get_token(session: Session, *, owner_id: str) -> OAuthTokenRow | None:
    """The stored token for an owner, decrypted. The DB row itself holds ciphertext; the
    returned row is expunged from the session so a caller can't accidentally flush the
    plaintext back to the database."""
    row = session.get(OAuthTokenRow, owner_id)
    if row is None:
        return None
    row.access_token = crypto.decrypt(row.access_token)
    if row.refresh_token:
        row.refresh_token = crypto.decrypt(row.refresh_token)
    session.expunge(row)
    return row


def delete_token(session: Session, *, owner_id: str) -> None:
    """Remove the stored token for an owner, if any — 'Disconnect Google account'.
    Idempotent: calling this when there's nothing stored is a no-op."""
    row = session.get(OAuthTokenRow, owner_id)
    if row is not None:
        session.delete(row)
        session.commit()


def is_expired(row: OAuthTokenRow, *, skew_seconds: int = 60) -> bool:
    """True if the access token is expired (or within skew of expiring)."""
    if row.expires_at is None:
        return False
    expires_at = row.expires_at
    if expires_at.tzinfo is None:  # SQLite round-trips naive datetimes
        expires_at = expires_at.replace(tzinfo=UTC)
    return _now() >= expires_at - timedelta(seconds=skew_seconds)
