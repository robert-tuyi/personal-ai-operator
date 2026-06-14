"""Token storage service tests — upsert semantics and expiry resolution."""

from datetime import UTC, datetime, timedelta

from app.services import oauth_tokens


def test_save_token_creates_row(session):
    row = oauth_tokens.save_token(
        session,
        owner_id="sub-123",
        email="me@example.com",
        token={
            "access_token": "at-1",
            "refresh_token": "rt-1",
            "token_type": "Bearer",
            "scope": "openid email",
            "expires_in": 3600,
        },
    )
    assert row.owner_id == "sub-123"
    assert row.access_token == "at-1"
    assert row.refresh_token == "rt-1"
    assert row.expires_at is not None
    assert not oauth_tokens.is_expired(row)


def test_save_token_upserts_and_preserves_refresh_token(session):
    """A refresh/re-auth often omits the refresh_token; we must not lose it."""
    oauth_tokens.save_token(
        session,
        owner_id="sub-123",
        email="me@example.com",
        token={"access_token": "at-1", "refresh_token": "rt-1", "expires_in": 3600},
    )
    # Second save (e.g. token refresh) has no refresh_token.
    row = oauth_tokens.save_token(
        session,
        owner_id="sub-123",
        email="me@example.com",
        token={"access_token": "at-2", "expires_in": 3600},
    )
    assert row.access_token == "at-2"
    assert row.refresh_token == "rt-1"  # preserved


def test_is_expired_with_past_expiry(session):
    row = oauth_tokens.save_token(
        session,
        owner_id="sub-123",
        email="me@example.com",
        token={
            "access_token": "at-1",
            "expires_at": int((datetime.now(UTC) - timedelta(hours=1)).timestamp()),
        },
    )
    assert oauth_tokens.is_expired(row)


def test_get_token_returns_none_when_absent(session):
    assert oauth_tokens.get_token(session, owner_id="nobody") is None
