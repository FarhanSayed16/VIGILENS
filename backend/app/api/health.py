"""Health / readiness endpoints."""

import logging
from typing import Any, Dict

from fastapi import APIRouter

from app.core.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


def _check_database() -> Dict[str, Any]:
    """Soft check — Phase 5 wires real engine; do not fail API boot."""
    settings = get_settings()
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 — soft health
        logger.debug("Database health soft-fail: %s", exc)
        return {"status": "unavailable", "detail": type(exc).__name__}


def _check_redis() -> Dict[str, Any]:
    """Soft check — Phase 11 hardens Redis usage."""
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=1)
        client.ping()
        client.close()
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001 — soft health
        logger.debug("Redis health soft-fail: %s", exc)
        return {"status": "unavailable", "detail": type(exc).__name__}


@router.get("/health")
def health() -> Dict[str, Any]:
    """
    API process liveness + soft dependency checks.

    Returns HTTP 200 whenever the API process is up (Phase 3 exit criterion).
    Nested database/redis may be unavailable until Docker/infra is running.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "use_fake_worker": bool(settings.use_fake_worker),
        "database": _check_database(),
        "redis": _check_redis(),
    }
