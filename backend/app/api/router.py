"""Mount all API routers."""

from fastapi import APIRouter

from app.api import (
    analysis,
    auth,
    events,
    export,
    health,
    jobs,
    media,
    modes,
    pulse,
    rooms,
    sessions,
    topics,
    windows,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(pulse.router)
api_router.include_router(rooms.router)
api_router.include_router(sessions.router)
api_router.include_router(topics.router)
api_router.include_router(modes.router)
api_router.include_router(media.router)
api_router.include_router(analysis.router)
api_router.include_router(jobs.router)
api_router.include_router(windows.router)
api_router.include_router(events.router)
api_router.include_router(export.router)

# Phase 15+: E2E checkpoint / real AIML…
