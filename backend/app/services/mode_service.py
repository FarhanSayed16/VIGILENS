"""Teaching mode timeline for a session."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import ModeChange, Session as SessionModel
from app.schemas.modes import ModeChangeCreate, ModeChangeListResponse, ModeChangeRead
from app.services.topic_service import elapsed_sec_for_session


def _ensure_session(db: Session, session_id: int) -> SessionModel:
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    return row


def _to_read(row: ModeChange) -> ModeChangeRead:
    return ModeChangeRead(
        id=row.id,
        session_id=row.session_id,
        start_sec=row.start_sec,
        mode=row.mode,  # type: ignore[arg-type]
    )


def list_modes(db: Session, session_id: int) -> ModeChangeListResponse:
    session = _ensure_session(db, session_id)
    rows = db.scalars(
        select(ModeChange)
        .where(ModeChange.session_id == session_id)
        .order_by(ModeChange.start_sec.asc(), ModeChange.id.asc())
    ).all()
    current = session.current_mode  # type: ignore[assignment]
    return ModeChangeListResponse(
        items=[_to_read(r) for r in rows],
        total=len(rows),
        current_mode=current,  # type: ignore[arg-type]
    )


def set_mode(db: Session, session_id: int, payload: ModeChangeCreate) -> ModeChangeRead:
    session = _ensure_session(db, session_id)

    if session.started_at is None:
        session.started_at = datetime.now(timezone.utc)

    start_sec = (
        float(payload.start_sec)
        if payload.start_sec is not None
        else elapsed_sec_for_session(session)
    )

    # Avoid duplicate consecutive mode at same second
    last = db.scalars(
        select(ModeChange)
        .where(ModeChange.session_id == session_id)
        .order_by(ModeChange.start_sec.desc(), ModeChange.id.desc())
        .limit(1)
    ).first()
    if last and last.mode == payload.mode and abs(last.start_sec - start_sec) < 0.5:
        _sync_current_mode(db, session)
        db.commit()
        db.refresh(last)
        return _to_read(last)

    row = ModeChange(
        session_id=session_id,
        start_sec=start_sec,
        mode=payload.mode,
    )
    db.add(row)
    db.flush()
    _sync_current_mode(db, session)
    db.commit()
    db.refresh(row)
    return _to_read(row)


def _sync_current_mode(db: Session, session: SessionModel) -> None:
    """current_mode = chronologically latest mode_change (by start_sec)."""
    latest = db.scalars(
        select(ModeChange)
        .where(ModeChange.session_id == session.id)
        .order_by(ModeChange.start_sec.desc(), ModeChange.id.desc())
        .limit(1)
    ).first()
    session.current_mode = latest.mode if latest else None


def resolve_mode_at(db: Session, session_id: int, t_sec: float) -> Optional[str]:
    """Latest mode with start_sec <= T."""
    _ensure_session(db, session_id)
    row = db.scalars(
        select(ModeChange)
        .where(ModeChange.session_id == session_id, ModeChange.start_sec <= t_sec)
        .order_by(ModeChange.start_sec.desc(), ModeChange.id.desc())
        .limit(1)
    ).first()
    return row.mode if row else None
