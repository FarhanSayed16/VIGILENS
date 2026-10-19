"""Persist worker windows/events, list results, warm timeline cache."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.cache.keys import (
    invalidate_session_caches,
    session_windows_key,
)
from app.core.exceptions import NotFoundError
from app.core.settings import get_settings
from app.db.models import Event, Session as SessionModel, Window
from app.schemas.results import (
    EventListResponse,
    EventPayload,
    EventRead,
    WindowListResponse,
    WindowPayload,
    WindowRead,
    WorkerResultPayload,
)
from app.services.summary_service import compute_summary_dict, warm_summary_cache

logger = logging.getLogger(__name__)


def _ensure_session(db: Session, session_id: int) -> SessionModel:
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    return row


def replace_session_results(
    db: Session,
    session_id: int,
    payload: WorkerResultPayload,
) -> Dict[str, int]:
    """
    Transactional rewrite: delete prior windows/events for session, insert new.
    Caller commits (or use persist_and_warm).
    """
    db.execute(delete(Event).where(Event.session_id == session_id))
    db.execute(delete(Window).where(Window.session_id == session_id))

    for w in payload.windows:
        db.add(_window_row(session_id, w))
    for e in payload.events:
        db.add(_event_row(session_id, e))

    db.flush()
    return {"window_count": len(payload.windows), "event_count": len(payload.events)}


def _window_row(session_id: int, w: WindowPayload) -> Window:
    return Window(
        session_id=session_id,
        start_sec=w.start_sec,
        end_sec=w.end_sec,
        topic_id=w.topic_id,
        teaching_mode=w.teaching_mode,
        expected_regions=w.expected_regions,
        usable_regions=w.usable_regions,
        coverage_pct=w.coverage_pct,
        ttoi=w.ttoi,
        ttoi_lo=w.ttoi_lo,
        ttoi_hi=w.ttoi_hi,
        head_down_cue_pct=w.head_down_cue_pct,
        hand_raise_events=w.hand_raise_events,
        candidate_decline=w.candidate_decline,
        dominant_cue=w.dominant_cue,
        data_quality_note=w.data_quality_note,
        seat_stats_json=w.seat_stats,
    )


def _event_row(session_id: int, e: EventPayload) -> Event:
    return Event(
        session_id=session_id,
        start_sec=e.start_sec,
        end_sec=e.end_sec,
        depth=e.depth,
        coverage_pct=e.coverage_pct,
        topic_id=e.topic_id,
        teaching_mode=e.teaching_mode,
        dominant_cue=e.dominant_cue,
        note=e.note,
        kind=e.kind or "orientation_decline",
        seat_ids_json=e.seat_ids,
        group_label=e.group_label,
        lecturer_feedback=e.lecturer_feedback,
    )


def clear_session_results(db: Session, session_id: int) -> None:
    db.execute(delete(Event).where(Event.session_id == session_id))
    db.execute(delete(Window).where(Window.session_id == session_id))
    db.flush()


def append_window(db: Session, session_id: int, w: WindowPayload) -> Window:
    """Append one live window (does not delete prior rows)."""
    row = _window_row(session_id, w)
    db.add(row)
    db.commit()
    db.refresh(row)
    invalidate_session_caches(session_id)
    return row


def replace_events_only(
    db: Session, session_id: int, events: List[EventPayload]
) -> int:
    db.execute(delete(Event).where(Event.session_id == session_id))
    for e in events:
        db.add(_event_row(session_id, e))
    db.commit()
    invalidate_session_caches(session_id)
    return len(events)


def set_event_feedback(
    db: Session, session_id: int, event_id: int, feedback: str
) -> Event:
    row = db.get(Event, event_id)
    if row is None or row.session_id != session_id:
        raise NotFoundError(f"Event {event_id} not found")
    row.lecturer_feedback = feedback
    db.commit()
    db.refresh(row)
    return row


def _window_to_read(row: Window) -> WindowRead:
    return WindowRead.model_validate(row)


def _event_to_read(row: Event) -> EventRead:
    return EventRead.model_validate(row)


def _fetch_windows_db(
    db: Session,
    session_id: int,
    *,
    min_coverage_pct: Optional[float] = None,
) -> List[WindowRead]:
    stmt = (
        select(Window)
        .where(Window.session_id == session_id)
        .order_by(Window.start_sec.asc(), Window.id.asc())
    )
    if min_coverage_pct is not None:
        stmt = stmt.where(Window.coverage_pct >= min_coverage_pct)
    rows = db.scalars(stmt).all()
    return [_window_to_read(r) for r in rows]


def warm_windows_cache(session_id: int, items: List[WindowRead]) -> None:
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(
            settings.redis_url, socket_connect_timeout=1, decode_responses=True
        )
        try:
            payload = [w.model_dump() for w in items]
            client.set(
                session_windows_key(session_id),
                json.dumps(payload),
                ex=60 * 60 * 24,
            )
        finally:
            client.close()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Windows cache warm soft-fail: %s", type(exc).__name__)


def get_cached_windows(session_id: int) -> Optional[List[dict]]:
    settings = get_settings()
    try:
        import redis

        client = redis.from_url(
            settings.redis_url, socket_connect_timeout=1, decode_responses=True
        )
        try:
            raw = client.get(session_windows_key(session_id))
            if not raw:
                return None
            data = json.loads(raw)
            return data if isinstance(data, list) else None
        finally:
            client.close()
    except Exception:  # noqa: BLE001
        return None


def list_windows(
    db: Session,
    session_id: int,
    *,
    min_coverage_pct: Optional[float] = None,
) -> WindowListResponse:
    _ensure_session(db, session_id)

    # Cache only for unfiltered full timeline
    if min_coverage_pct is None:
        cached = get_cached_windows(session_id)
        if cached is not None:
            items = [WindowRead.model_validate(x) for x in cached]
            return WindowListResponse(
                session_id=session_id,
                items=items,
                total=len(items),
                cached=True,
            )

    items = _fetch_windows_db(db, session_id, min_coverage_pct=min_coverage_pct)
    if min_coverage_pct is None and items:
        warm_windows_cache(session_id, items)

    return WindowListResponse(
        session_id=session_id,
        items=items,
        total=len(items),
        cached=False,
    )


def list_events(db: Session, session_id: int) -> EventListResponse:
    _ensure_session(db, session_id)
    rows = db.scalars(
        select(Event)
        .where(Event.session_id == session_id)
        .order_by(Event.start_sec.asc(), Event.id.asc())
    ).all()
    items = [_event_to_read(r) for r in rows]
    return EventListResponse(session_id=session_id, items=items, total=len(items))


def persist_and_warm(
    db: Session,
    session_id: int,
    payload: WorkerResultPayload,
) -> Dict[str, Any]:
    """Rewrite results, commit, warm summary + windows caches."""
    invalidate_session_caches(session_id)
    replace_session_results(db, session_id, payload)
    summary = compute_summary_dict(db, session_id)
    windows = _fetch_windows_db(db, session_id)
    db.commit()
    warm_summary_cache(session_id, summary)
    warm_windows_cache(session_id, windows)
    return summary
