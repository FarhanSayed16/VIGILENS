"""Redis key helpers and session cache invalidate/read."""

from __future__ import annotations

import logging
from typing import Optional

from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def job_status_key(job_id: int) -> str:
    return f"job:{job_id}:status"


def session_summary_key(session_id: int) -> str:
    return f"session:{session_id}:summary"


def session_windows_key(session_id: int) -> str:
    return f"session:{session_id}:windows"


def analysis_lock_key() -> str:
    return "lock:analysis"


def invalidate_session_caches(session_id: int) -> None:
    """
    Soft-delete Redis keys for a session.

    Safe when Redis is down — logs and continues (DB remains source of truth).
    """
    settings = get_settings()
    keys = [
        session_summary_key(session_id),
        session_windows_key(session_id),
    ]
    try:
        import redis

        client = redis.from_url(settings.redis_url, socket_connect_timeout=1)
        try:
            client.delete(*keys)
            logger.debug("Invalidated session caches for session_id=%s", session_id)
        finally:
            client.close()
    except Exception as exc:  # noqa: BLE001 — soft stub
        logger.debug(
            "Session cache invalidate soft-fail session_id=%s: %s",
            session_id,
            type(exc).__name__,
        )


def get_cached_summary(session_id: int) -> Optional[dict]:
    """Optional read of cached summary; returns None if missing or Redis down."""
    settings = get_settings()
    try:
        import redis
        import json

        client = redis.from_url(settings.redis_url, socket_connect_timeout=1)
        try:
            raw = client.get(session_summary_key(session_id))
            if not raw:
                return None
            return json.loads(raw)
        finally:
            client.close()
    except Exception:  # noqa: BLE001
        return None
