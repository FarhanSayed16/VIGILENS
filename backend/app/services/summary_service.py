"""Build and serve session summary (DB + Redis cache)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.cache.keys import get_cached_summary, session_summary_key
from app.core.exceptions import NotFoundError
from app.core.settings import get_settings
from app.db.enums import DataQualityNote
from app.db.models import Event, Session as SessionModel, Window
from app.schemas.sessions import SessionSummary

logger = logging.getLogger(__name__)


def compute_summary_dict(db: Session, session_id: int) -> Dict[str, Any]:
    win_count = int(
        db.scalar(select(func.count()).select_from(Window).where(Window.session_id == session_id))
        or 0
    )
    evt_count = int(
        db.scalar(select(func.count()).select_from(Event).where(Event.session_id == session_id))
        or 0
    )
    mean_ttoi = db.scalar(
        select(func.avg(Window.ttoi)).where(
            Window.session_id == session_id, Window.ttoi.is_not(None)
        )
    )
    mean_cov = db.scalar(
        select(func.avg(Window.coverage_pct)).where(
            Window.session_id == session_id, Window.coverage_pct.is_not(None)
        )
    )
    insuff = int(
        db.scalar(
            select(func.count())
            .select_from(Window)
            .where(
                Window.session_id == session_id,
                Window.data_quality_note == DataQualityNote.INSUFFICIENT_COVERAGE.value,
            )
        )
        or 0
    )
    partial = int(
        db.scalar(
            select(func.count())
            .select_from(Window)
            .where(
                Window.session_id == session_id,
                Window.data_quality_note == DataQualityNote.PARTIAL_WINDOW.value,
            )
        )
        or 0
    )
    declines = int(
        db.scalar(
            select(func.count())
            .select_from(Window)
            .where(Window.session_id == session_id, Window.candidate_decline.is_(True))
        )
        or 0
    )
    duration = db.scalar(
        select(func.max(Window.end_sec)).where(Window.session_id == session_id)
    )

    return {
        "mean_ttoi": float(mean_ttoi) if mean_ttoi is not None else None,
        "mean_coverage": float(mean_cov) if mean_cov is not None else None,
        "event_count": evt_count,
        "window_count": win_count,
        "insufficient_coverage_windows": insuff,
        "partial_windows": partial,
        "candidate_decline_windows": declines,
        "duration_sec": float(duration) if duration is not None else None,
        "note": "Class-level aggregates from analysis. Not attention or emotion scores.",
    }


def warm_summary_cache(session_id: int, summary: Dict[str, Any]) -> None:
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(
            settings.redis_url, socket_connect_timeout=1, decode_responses=True
        )
        try:
            client.set(session_summary_key(session_id), json.dumps(summary), ex=60 * 60 * 24)
        finally:
            client.close()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Summary cache warm soft-fail: %s", type(exc).__name__)


def get_summary(db: Session, session_id: int) -> SessionSummary:
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")

    cached = get_cached_summary(session_id)
    if cached and int(cached.get("window_count") or 0) > 0:
        return SessionSummary(
            session_id=session_id,
            status=row.status,  # type: ignore[arg-type]
            mean_ttoi=cached.get("mean_ttoi"),
            mean_coverage=cached.get("mean_coverage"),
            event_count=int(cached.get("event_count") or 0),
            window_count=int(cached.get("window_count") or 0),
            insufficient_coverage_windows=int(
                cached.get("insufficient_coverage_windows") or 0
            ),
            partial_windows=int(cached.get("partial_windows") or 0),
            candidate_decline_windows=int(cached.get("candidate_decline_windows") or 0),
            duration_sec=cached.get("duration_sec"),
            cached=True,
            note=str(cached.get("note") or ""),
        )

    computed = compute_summary_dict(db, session_id)
    if computed["window_count"] == 0:
        return SessionSummary(
            session_id=session_id,
            status=row.status,  # type: ignore[arg-type]
            note="Summary available after analysis.",
        )

    warm_summary_cache(session_id, computed)
    return SessionSummary(
        session_id=session_id,
        status=row.status,  # type: ignore[arg-type]
        mean_ttoi=computed.get("mean_ttoi"),
        mean_coverage=computed.get("mean_coverage"),
        event_count=int(computed.get("event_count") or 0),
        window_count=int(computed.get("window_count") or 0),
        insufficient_coverage_windows=int(
            computed.get("insufficient_coverage_windows") or 0
        ),
        partial_windows=int(computed.get("partial_windows") or 0),
        candidate_decline_windows=int(computed.get("candidate_decline_windows") or 0),
        duration_sec=computed.get("duration_sec"),
        cached=False,
        note=str(computed.get("note") or ""),
    )
