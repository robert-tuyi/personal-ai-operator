from fastapi import APIRouter

from app.api.v1 import approvals, auth, brief, calendar, drafts, followups, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(brief.router, tags=["brief"])
api_router.include_router(calendar.router, tags=["calendar"])
api_router.include_router(drafts.router, tags=["drafts"])
api_router.include_router(approvals.router, tags=["approvals"])
api_router.include_router(followups.router, tags=["followups"])
