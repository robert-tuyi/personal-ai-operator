from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.approval import ApprovalError
from app.db.session import init_db
from app.integrations.google import register_action_executors


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    register_action_executors()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Personal AI Operator", version="0.1.0", lifespan=lifespan)
    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(ApprovalError)
    async def _approval_error(_: Request, exc: ApprovalError) -> JSONResponse:
        # Lifecycle violations (e.g. executing an unapproved action) are client errors.
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    return app


app = create_app()
