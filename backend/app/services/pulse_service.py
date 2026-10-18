"""Anonymous pulse: rate-limit, stamp active topic, store score only."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.core.settings import get_settings
from app.db.models import PulseResponse, Session as SessionModel
from app.schemas.pulse import PulseAccepted, PulseSubmit
from app.services.topic_service import elapsed_sec_for_session, resolve_active_topic_id_at

logger = logging.getLogger(__name__)

# Soft limits: N submits per IP+session per window
RATE_LIMIT_COUNT = 12
RATE_LIMIT_WINDOW_SEC = 60


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client and request.client.host:
        return request.client.host[:64]
    return "unknown"


def _rate_limit_or_raise(session_id: int, ip: str) -> None:
    settings = get_settings()
    key = f"pulse:rl:{session_id}:{ip}"
    try:
        import redis

        client = redis.from_url(
            settings.redis_url, socket_connect_timeout=1, decode_responses=True
        )
        try:
            count = client.incr(key)
            if count == 1:
                client.expire(key, RATE_LIMIT_WINDOW_SEC)
            if count > RATE_LIMIT_COUNT:
                raise AppError(
                    "Too many pulse submissions — try again shortly",
                    status_code=429,
                    code="rate_limited",
                    details={"retry_after_sec": RATE_LIMIT_WINDOW_SEC},
                )
        finally:
            client.close()
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001 — fail closed if Redis down
        logger.warning("Pulse rate-limit unavailable: %s", type(exc).__name__)
        raise AppError(
            "Pulse temporarily unavailable — rate limiter offline",
            status_code=503,
            code="pulse_rate_limit_unavailable",
            details={"type": type(exc).__name__},
        ) from exc


def submit_pulse(
    db: Session,
    session_id: int,
    body: PulseSubmit,
    request: Request,
) -> PulseAccepted:
    from app.db.enums import SourceType

    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")

    _rate_limit_or_raise(session_id, _client_ip(request))

    # Upload sessions use media-relative topic times; live pulse wall-clock ≠ video.
    # Stamp topic only for live sources (webcam / phone).
    topic_id: Optional[int] = None
    if row.source_type != SourceType.UPLOAD.value:
        t_sec = elapsed_sec_for_session(row)
        topic_id = resolve_active_topic_id_at(db, session_id, t_sec)

    pulse = PulseResponse(
        session_id=session_id,
        topic_id=topic_id,
        score_1_to_5=body.score_1_to_5,
    )
    db.add(pulse)
    db.commit()
    db.refresh(pulse)

    return PulseAccepted(
        session_id=session_id,
        score_1_to_5=pulse.score_1_to_5,
        topic_id=pulse.topic_id,
        created_at=pulse.created_at,
    )
