from fastapi import APIRouter

from app.api.v1 import approvals, brief, drafts, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(brief.router, tags=["brief"])
api_router.include_router(drafts.router, tags=["drafts"])
api_router.include_router(approvals.router, tags=["approvals"])
