from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.approval import ApprovalError
from app.core.csrf import CSRFMiddleware
from app.db.session import init_db
from app.integrations.google import register_action_executors


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    register_action_executors()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Personal AI Operator", version="0.1.0", lifespan=lifespan)

    # Signed session cookie carries the logged-in Google user's identity (see core/deps.py).
    # The secret comes from env (config.py); never hardcode it for real deployments.
    # ADR 0003: https_only outside development (never send the cookie over plain HTTP,
    # where it could leak in the clear), same_site="lax" made explicit, and a shorter
    # max_age than Starlette's 14-day default so a stolen cookie doesn't stay valid as long.
    settings = get_settings()
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        https_only=settings.app_env != "development",
        same_site="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    # CSRF defense-in-depth (ADR 0003) — see core/csrf.py for why this exists alongside
    # SameSite=Lax rather than instead of it.
    app.add_middleware(CSRFMiddleware)

    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(ApprovalError)
    async def _approval_error(_: Request, exc: ApprovalError) -> JSONResponse:
        # Lifecycle violations (e.g. executing an unapproved action) are client errors.
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    return app


app = create_app()
