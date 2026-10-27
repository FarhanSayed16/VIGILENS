"""Shared Redis helpers: connection, analysis lock, job status payloads."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from app.cache.keys import (
    analysis_lock_key,
    job_status_key,
    live_ingest_key,
    live_ingest_seq_key,
    live_preview_key,
    live_snapshot_key,
    live_stop_key,
)
from app.core.exceptions import AppError, ConflictError
from app.core.settings import get_settings

logger = logging.getLogger(__name__)

LOCK_TTL_SEC = 60 * 60  # 1 hour safety TTL
JOB_STATUS_TTL_SEC = 60 * 60 * 24


def get_redis(*, decode_responses: bool = True):
    """Return a Redis client or raise AppError if unreachable.

    Use ``decode_responses=False`` for binary values (live JPEG preview).
    The default client is string-mode for JSON status keys.
    """
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            decode_responses=decode_responses,
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


def refresh_analysis_lock(job_id: int, *, ttl: int = LOCK_TTL_SEC) -> bool:
    """Extend lock TTL if this job still holds it (prevents orphan RUNNING on long jobs)."""
    client = get_redis()
    try:
        key = analysis_lock_key()
        holder = client.get(key)
        if holder is None or str(holder) != str(job_id):
            return False
        client.expire(key, ttl)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("Lock refresh failed for job %s: %s", job_id, type(exc).__name__)
        return False
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


LIVE_SNAPSHOT_TTL_SEC = 60 * 60 * 6


def set_live_snapshot(session_id: int, payload: Dict[str, Any]) -> None:
    try:
        client = get_redis()
    except AppError:
        return
    try:
        client.set(
            live_snapshot_key(session_id),
            json.dumps(payload),
            ex=LIVE_SNAPSHOT_TTL_SEC,
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("live snapshot set failed: %s", type(exc).__name__)
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


def get_live_snapshot(session_id: int) -> Optional[Dict[str, Any]]:
    try:
        client = get_redis()
    except AppError:
        return None
    try:
        raw = client.get(live_snapshot_key(session_id))
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


LIVE_PREVIEW_TTL_SEC = 120


def set_live_preview_jpeg(session_id: int, jpeg: bytes) -> None:
    """Store latest worker preview frame (binary JPEG — requires bytes client)."""
    if not jpeg:
        return
    try:
        # Must NOT use decode_responses=True — JPEG is binary and would be dropped
        client = get_redis(decode_responses=False)
    except AppError:
        return
    try:
        client.set(live_preview_key(session_id), jpeg, ex=LIVE_PREVIEW_TTL_SEC)
    except Exception as exc:  # noqa: BLE001
        logger.warning("live preview set failed: %s", type(exc).__name__)
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


def get_live_preview_jpeg(session_id: int) -> Optional[bytes]:
    try:
        client = get_redis(decode_responses=False)
    except AppError:
        return None
    try:
        raw = client.get(live_preview_key(session_id))
        if not raw:
            return None
        if isinstance(raw, memoryview):
            return raw.tobytes()
        if isinstance(raw, bytearray):
            return bytes(raw)
        if isinstance(raw, bytes):
            return raw
        # Legacy string garbage from decode_responses=True era — ignore
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("live preview get failed: %s", type(exc).__name__)
        return None
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


_ingest_client = None


def _ingest_redis():
    """Reuse one binary client — the phone posts several frames a second."""
    global _ingest_client
    if _ingest_client is not None:
        try:
            _ingest_client.ping()
            return _ingest_client
        except Exception:  # noqa: BLE001
            try:
                _ingest_client.close()
            except Exception:  # noqa: BLE001
                pass
            _ingest_client = None
    _ingest_client = get_redis(decode_responses=False)
    return _ingest_client


def set_live_ingest_jpeg(session_id: int, jpeg: bytes) -> None:
    """Latest phone-browser JPEG. The live worker reads this instead of OpenCV."""
    if not jpeg:
        return
    client = _ingest_redis()
    pipe = client.pipeline()
    pipe.set(live_ingest_key(session_id), jpeg, ex=12)
    pipe.incr(live_ingest_seq_key(session_id))
    pipe.expire(live_ingest_seq_key(session_id), 30)
    pipe.execute()


def get_live_ingest_jpeg(session_id: int) -> tuple[Optional[bytes], int]:
    try:
        client = _ingest_redis()
        jpeg, seq = client.mget(
            live_ingest_key(session_id),
            live_ingest_seq_key(session_id),
        )
    except Exception:  # noqa: BLE001
        return None, 0
    n = 0
    if seq is not None:
        try:
            n = int(seq)
        except (TypeError, ValueError):
            n = 0
    if isinstance(jpeg, memoryview):
        jpeg = jpeg.tobytes()
    elif isinstance(jpeg, bytearray):
        jpeg = bytes(jpeg)
    elif not isinstance(jpeg, bytes):
        jpeg = None
    return jpeg, n


def request_live_stop(session_id: int) -> None:
    try:
        client = get_redis()
    except AppError:
        return
    try:
        client.set(live_stop_key(session_id), "1", ex=LIVE_SNAPSHOT_TTL_SEC)
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


def clear_live_stop(session_id: int) -> None:
    try:
        client = get_redis()
    except AppError:
        return
    try:
        client.delete(live_stop_key(session_id))
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass


def live_stop_requested(session_id: int) -> bool:
    try:
        client = get_redis()
    except AppError:
        return False
    try:
        return bool(client.get(live_stop_key(session_id)))
    except Exception:  # noqa: BLE001
        return False
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001
            pass
