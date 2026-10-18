"""Shared Redis helpers: connection, analysis lock, job status payloads."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.cache.keys import analysis_lock_key, job_status_key
from app.core.exceptions import AppError, ConflictError
from app.core.settings import get_settings

logger = logging.getLogger(__name__)

LOCK_TTL_SEC = 60 * 60  # 1 hour safety TTL
JOB_STATUS_TTL_SEC = 60 * 60 * 24


def get_redis():
    """Return a Redis client or raise AppError if unreachable."""
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            decode_responses=True,
        )
        client.ping()
        return client
    except Exception as exc:  # noqa: BLE001
        raise AppError(
            "Redis is unavailable — cannot start or track analysis jobs",
            status_code=503,
            code="redis_unavailable",
            details={"type": type(exc).__name__},
        ) from exc


def try_acquire_analysis_lock(job_id: int, *, ttl: int = LOCK_TTL_SEC) -> bool:
    client = get_redis()
    try:
        ok = client.set(analysis_lock_key(), str(job_id), nx=True, ex=ttl)
        return bool(ok)
    finally:
        client.close()


def get_analysis_lock_holder() -> Optional[int]:
    client = get_redis()
    try:
        raw = client.get(analysis_lock_key())
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None
    finally:
        client.close()


def release_analysis_lock(job_id: int) -> None:
    """Release lock only if this job still owns it."""
    client = get_redis()
    try:
        key = analysis_lock_key()
        holder = client.get(key)
        if holder is not None and str(holder) == str(job_id):
            client.delete(key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to release analysis lock for job %s: %s", job_id, type(exc).__name__)
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


def force_clear_analysis_lock() -> None:
    client = get_redis()
    try:
        client.delete(analysis_lock_key())
    finally:
        client.close()


def set_job_status_cache(job_id: int, payload: Dict[str, Any]) -> None:
    client = get_redis()
    try:
        client.set(
            job_status_key(job_id),
            json.dumps(payload),
            ex=JOB_STATUS_TTL_SEC,
        )
    finally:
        client.close()


def get_job_status_cache(job_id: int) -> Optional[Dict[str, Any]]:
    try:
        client = get_redis()
    except AppError:
        return None
    try:
        raw = client.get(job_status_key(job_id))
        if not raw:
            return None
        return json.loads(raw)
    except Exception:  # noqa: BLE001
        return None
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


def require_lock_or_conflict(job_id: int) -> None:
    """Acquire lock or raise 409 if another job holds it."""
    if try_acquire_analysis_lock(job_id):
        return
    holder = get_analysis_lock_holder()
    raise ConflictError(
        "Another analysis job is already running on this machine",
        details={"lock_holder_job_id": holder},
    )
