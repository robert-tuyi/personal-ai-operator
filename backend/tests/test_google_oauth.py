"""OAuth refresh tests — fully mocked httpx, never hits Google's token endpoint.

Covers access_token_for's refresh-on-expiry path: a fresh access token is stored while the
existing refresh token is preserved, and a failed refresh surfaces as GoogleAuthError.
"""

import time

import httpx
import pytest

from app.integrations import google_oauth
from app.integrations.google_oauth import GoogleAuthError
from app.services import oauth_tokens


class _FakeResponse:
    def __init__(self, json_data: dict, status_code: int = 200):
        self._json = json_data
        self.status_code = status_code

    def json(self) -> dict:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)


def _store_expired_token(session):
    """Persist an already-expired token with a refresh token for the owner."""
    return oauth_tokens.save_token(
        session,
        owner_id="owner",
        email="me@example.com",
        token={
            "access_token": "old-at",
            "refresh_token": "rt-keep",
            "expires_at": int(time.time()) - 3600,
        },
    )


def test_refresh_on_expiry_stores_new_token_and_preserves_refresh_token(session, monkeypatch):
    _store_expired_token(session)
    # Google's refresh response omits refresh_token.
    monkeypatch.setattr(
        google_oauth.httpx,
        "post",
        lambda *a, **k: _FakeResponse({"access_token": "new-at", "expires_in": 3600}),
    )

    token = google_oauth.access_token_for(session, owner_id="owner")

    assert token == "new-at"
    row = oauth_tokens.get_token(session, owner_id="owner")
    assert row.access_token == "new-at"
    assert row.refresh_token == "rt-keep"  # preserved across refresh


def test_failed_refresh_raises_google_auth_error(session, monkeypatch):
    _store_expired_token(session)
    monkeypatch.setattr(
        google_oauth.httpx,
        "post",
        lambda *a, **k: _FakeResponse({}, status_code=400),
    )

    with pytest.raises(GoogleAuthError):
        google_oauth.access_token_for(session, owner_id="owner")


# --- disconnect ---------------------------------------------------------------------


def test_disconnect_revokes_refresh_token_with_google_and_deletes_local_row(session, monkeypatch):
    _store_expired_token(session)  # has both access_token and refresh_token
    calls = []
    monkeypatch.setattr(
        google_oauth.httpx,
        "post",
        lambda url, **k: calls.append((url, k)) or _FakeResponse({}),
    )

    google_oauth.disconnect(session, owner_id="owner")

    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == google_oauth.REVOKE_URL
    # Revoking the refresh token invalidates the whole grant, not just one access token.
    assert kwargs["params"]["token"] == "rt-keep"
    assert oauth_tokens.get_token(session, owner_id="owner") is None


def test_disconnect_falls_back_to_access_token_when_no_refresh_token(session, monkeypatch):
    oauth_tokens.save_token(
        session, owner_id="owner", email="me@example.com", token={"access_token": "at-only"}
    )
    calls = []
    monkeypatch.setattr(
        google_oauth.httpx,
        "post",
        lambda url, **k: calls.append((url, k)) or _FakeResponse({}),
    )

    google_oauth.disconnect(session, owner_id="owner")

    assert calls[0][1]["params"]["token"] == "at-only"
    assert oauth_tokens.get_token(session, owner_id="owner") is None


def test_disconnect_deletes_local_row_even_if_google_revoke_fails(session, monkeypatch):
    """A network hiccup or a token Google already considers invalid must not block the
    local disconnect."""
    _store_expired_token(session)

    def _raise(*a, **k):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(google_oauth.httpx, "post", _raise)

    google_oauth.disconnect(session, owner_id="owner")  # must not raise

    assert oauth_tokens.get_token(session, owner_id="owner") is None


def test_disconnect_is_a_noop_when_nothing_stored(session, monkeypatch):
    calls = []
    monkeypatch.setattr(google_oauth.httpx, "post", lambda *a, **k: calls.append(1))

    google_oauth.disconnect(session, owner_id="nobody")  # must not raise

    assert calls == []  # nothing to revoke
