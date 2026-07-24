"""OAuth login route tests — mocked Authlib client, no live Google.

We verify the callback persists the token and sets the session identity, and that
protected routes require a session.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import auth
from app.config import get_settings
from app.db.session import get_session
from app.main import create_app
from app.services import oauth_tokens


@pytest.fixture
def client(session):
    """A TestClient whose DB session is the in-memory test session."""

    def _override_get_session():
        yield session

    app = create_app()
    app.dependency_overrides[get_session] = _override_get_session
    return TestClient(app)


def test_me_unauthenticated(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json() == {"authenticated": False, "owner_id": None, "email": None}


def test_brief_requires_login(client):
    resp = client.get("/api/v1/brief")
    assert resp.status_code == 401


def test_followups_requires_login(client):
    resp = client.get("/api/v1/followups")
    assert resp.status_code == 401


def test_callback_stores_token_and_sets_session(client, monkeypatch, session):
    fake_token = {
        "access_token": "at-1",
        "refresh_token": "rt-1",
        "token_type": "Bearer",
        "scope": get_settings().google_oauth_scopes,  # full grant -> a genuine successful login
        "expires_in": 3600,
        "userinfo": {"sub": "sub-999", "email": "me@example.com"},
    }

    class _FakeClient:
        async def authorize_access_token(self, request):
            return fake_token

    class _FakeOAuth:
        def create_client(self, name):
            return _FakeClient()

    monkeypatch.setattr(auth, "get_oauth", lambda: _FakeOAuth())

    resp = client.get("/api/v1/auth/callback", follow_redirects=False)
    assert resp.status_code in (302, 307)

    # Token persisted, owner-scoped by the Google "sub".
    row = oauth_tokens.get_token(session, owner_id="sub-999")
    assert row is not None
    assert row.access_token == "at-1"
    assert row.email == "me@example.com"

    # Session now identifies the user.
    me = client.get("/api/v1/auth/me")
    assert me.json() == {
        "authenticated": True,
        "owner_id": "sub-999",
        "email": "me@example.com",
    }

    # ADR 0003: cookie hardening took effect. In dev (app_env=development, the default
    # here) https_only=False so the cookie must still work over TestClient's plain HTTP —
    # but same_site is explicitly set regardless of environment.
    set_cookie = resp.headers.get("set-cookie", "").lower()
    assert "samesite=lax" in set_cookie
    assert "secure" not in set_cookie


def _fake_oauth_with_scope(scope: str | None):
    fake_token = {
        "access_token": "at-1",
        "refresh_token": "rt-1",
        "expires_in": 3600,
        "userinfo": {"sub": "sub-999", "email": "me@example.com"},
    }
    if scope is not None:
        fake_token["scope"] = scope

    class _FakeClient:
        async def authorize_access_token(self, request):
            return fake_token

    class _FakeOAuth:
        def create_client(self, name):
            return _FakeClient()

    return _FakeOAuth()


def test_callback_rejects_a_partial_scope_grant(client, monkeypatch):
    """ADR 0003: don't silently treat a partial grant as full access."""
    monkeypatch.setattr(
        auth, "get_oauth", lambda: _fake_oauth_with_scope("openid email")
    )

    resp = client.get("/api/v1/auth/callback", follow_redirects=False)

    assert resp.status_code == 400
    assert "gmail" in resp.json()["detail"].lower()
    # No session should have been established off a rejected callback.
    assert client.get("/api/v1/auth/me").json()["authenticated"] is False


def test_callback_accepts_when_scope_is_omitted(client, monkeypatch):
    """RFC 6749 §5.1: the token response omits `scope` entirely when it matches what was
    requested — an absent field must not be treated as an empty (fully missing) grant."""
    monkeypatch.setattr(auth, "get_oauth", lambda: _fake_oauth_with_scope(None))

    resp = client.get("/api/v1/auth/callback", follow_redirects=False)

    assert resp.status_code in (302, 307)
