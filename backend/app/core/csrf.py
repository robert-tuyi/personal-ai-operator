"""CSRF defense-in-depth (ADR 0003) via the double-submit cookie pattern.

SameSite="lax" on the session cookie (main.py) already blocks the classic cross-site form
POST — Lax cookies aren't sent on a cross-site POST at all — but this app doesn't rely on
that alone for state-changing requests (approve/reject/execute a send, among others): a
second, non-cookie-based check is worth it given what's at stake.

Every response ensures a non-HttpOnly `csrf_token` cookie is set (it must be readable by the
frontend JS so it can echo it back — see frontend/src/lib/api/client.ts). Every
POST/PUT/PATCH/DELETE request must carry a matching `X-CSRF-Token` header, or it is refused
with 403. A same-site attacker page can trick a browser into sending the session cookie
automatically, but it cannot read this cookie's value to put in a header — only same-origin
JS can.
"""

import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings

COOKIE_NAME = "csrf_token"
HEADER_NAME = "x-csrf-token"
_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        cookie_token = request.cookies.get(COOKIE_NAME)

        if request.method in _UNSAFE_METHODS:
            header_token = request.headers.get(HEADER_NAME)
            if not cookie_token or not header_token or not secrets.compare_digest(
                cookie_token, header_token
            ):
                response = JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid"},
                )
                # Seed the cookie even on a refusal — a client that POSTs before ever
                # making a GET (so has no token yet) can still recover on retry rather
                # than being stuck unable to ever obtain one.
                self._ensure_cookie(response, cookie_token)
                return response

        response = await call_next(request)
        self._ensure_cookie(response, cookie_token)
        return response

    @staticmethod
    def _ensure_cookie(response: Response, cookie_token: str | None) -> None:
        if cookie_token:
            return
        settings = get_settings()
        response.set_cookie(
            COOKIE_NAME,
            secrets.token_urlsafe(32),
            httponly=False,  # must be readable by frontend JS to echo back as a header
            samesite="lax",
            secure=settings.app_env != "development",
            max_age=60 * 60 * 24 * 7,
        )
