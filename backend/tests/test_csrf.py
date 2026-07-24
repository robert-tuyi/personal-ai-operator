"""CSRF middleware tests (ADR 0003) — double-submit cookie pattern.

Uses a real TestClient against the actual app so the middleware genuinely runs, not a
mocked stand-in. POST /auth/logout is the target: it needs no auth or body, so the test
isolates CSRF behavior from anything else.
"""

from fastapi.testclient import TestClient

from app.core.csrf import COOKIE_NAME, HEADER_NAME
from app.db.session import get_session
from app.main import create_app


def _client(session) -> TestClient:
    def _override_get_session():
        yield session

    app = create_app()
    app.dependency_overrides[get_session] = _override_get_session
    return TestClient(app)


def test_get_request_issues_csrf_cookie(session):
    client = _client(session)
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert COOKIE_NAME in resp.cookies


def test_post_without_csrf_token_is_refused(session):
    client = _client(session)
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 403


def test_rejected_post_still_seeds_the_cookie(session):
    """Regression test: a client whose very first request is a POST (no prior GET, so no
    cookie yet — e.g. a page with no on-mount fetch) must be able to recover on retry
    rather than being permanently stuck with no way to ever obtain a token."""
    client = _client(session)
    first = client.post("/api/v1/auth/logout")
    assert first.status_code == 403
    assert COOKIE_NAME in first.cookies

    token = client.cookies.get(COOKIE_NAME)
    retry = client.post("/api/v1/auth/logout", headers={HEADER_NAME: token})
    assert retry.status_code == 200


def test_post_with_mismatched_csrf_token_is_refused(session):
    client = _client(session)
    client.get("/api/v1/auth/me")  # picks up the csrf cookie
    resp = client.post("/api/v1/auth/logout", headers={HEADER_NAME: "wrong-value"})
    assert resp.status_code == 403


def test_post_with_matching_csrf_token_succeeds(session):
    client = _client(session)
    client.get("/api/v1/auth/me")  # picks up the csrf cookie
    token = client.cookies.get(COOKIE_NAME)

    resp = client.post("/api/v1/auth/logout", headers={HEADER_NAME: token})
    assert resp.status_code == 200
