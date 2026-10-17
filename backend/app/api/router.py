"""Mount all API routers."""

from fastapi import APIRouter

from app.api import auth, health, pulse, rooms

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(pulse.router)
api_router.include_router(rooms.router)

# Phase 8+: sessions, topics, modes, media, analysis, …
