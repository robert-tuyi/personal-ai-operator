"""OAuth login route tests — mocked Authlib client, no live Google.

We verify the callback persists the token and sets the session identity, and that
protected routes require a session.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.v1 import auth
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
        "scope": "openid email",
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
