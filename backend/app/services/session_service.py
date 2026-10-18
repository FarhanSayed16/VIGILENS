"""Session lifecycle: list, create, get, summary stub, cascade delete."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.cache.keys import invalidate_session_caches
from app.core.exceptions import NotFoundError
from app.core.settings import get_settings
from app.db.enums import SessionStatus
from app.db.models import RoomConfig, Session as SessionModel
from app.schemas.sessions import (
    SessionCreate,
    SessionListResponse,
    SessionRead,
    SessionSummary,
)
from app.services import summary_service

logger = logging.getLogger(__name__)


def _public_video_path(video_path: Optional[str]) -> Optional[str]:
    """Expose only a path relative to UPLOAD_DIR (no absolute FS leaks)."""
    if not video_path:
        return None
    settings = get_settings()
    try:
        path = Path(video_path)
        root = Path(settings.upload_dir).resolve()
        if path.is_absolute():
            return path.resolve().relative_to(root).as_posix()
        # Already relative — reject traversal segments
        rel = Path(video_path)
        if ".." in rel.parts:
            return None
        return rel.as_posix()
    except Exception:  # noqa: BLE001
        return None


def _redact_source_url(url: Optional[str]) -> Optional[str]:
    """Strip embedded user:password from RTSP/HTTP URLs in API responses."""
    if not url:
        return None
    try:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(url)
        if not parsed.username and not parsed.password:
            return url
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        netloc = host
        return urlunparse(
            (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
        )
    except Exception:  # noqa: BLE001
        return url


def _to_read(row: SessionModel) -> SessionRead:
    room_name = row.room_config.name if row.room_config else None
    return SessionRead(
        id=row.id,
        title=row.title,
        room_config_id=row.room_config_id,
        room_name=room_name,
        source_type=row.source_type,  # type: ignore[arg-type]
        status=row.status,  # type: ignore[arg-type]
        source_url=_redact_source_url(row.source_url),
        video_path=_public_video_path(row.video_path),
        current_mode=row.current_mode,
        started_at=row.started_at,
        ended_at=row.ended_at,
        created_at=row.created_at,
        has_video=bool(row.video_path),
    )


def list_sessions(
    db: Session,
    *,
    room_config_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> SessionListResponse:
    stmt = select(SessionModel).options(joinedload(SessionModel.room_config))
    count_stmt = select(func.count()).select_from(SessionModel)

    if room_config_id is not None:
        stmt = stmt.where(SessionModel.room_config_id == room_config_id)
        count_stmt = count_stmt.where(SessionModel.room_config_id == room_config_id)
    if status is not None:
        stmt = stmt.where(SessionModel.status == status)
        count_stmt = count_stmt.where(SessionModel.status == status)

    total = int(db.scalar(count_stmt) or 0)
    rows = db.scalars(
        stmt.order_by(SessionModel.id.desc()).offset(offset).limit(min(limit, 200))
    ).unique().all()
    return SessionListResponse(items=[_to_read(r) for r in rows], total=total)


def get_session(db: Session, session_id: int) -> SessionRead:
    row = db.scalars(
        select(SessionModel)
        .options(joinedload(SessionModel.room_config))
        .where(SessionModel.id == session_id)
    ).unique().first()
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    return _to_read(row)


def create_session(db: Session, payload: SessionCreate) -> SessionRead:
    room = db.get(RoomConfig, payload.room_config_id)
    if room is None:
        raise NotFoundError(f"Room {payload.room_config_id} not found")

    row = SessionModel(
        title=payload.title,
        room_config_id=payload.room_config_id,
        source_type=payload.source_type,
        source_url=payload.source_url,
        started_at=payload.started_at,
        status=SessionStatus.DRAFT.value,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    # Reload with room relationship for room_name
    return get_session(db, row.id)


def get_summary(db: Session, session_id: int) -> SessionSummary:
    return summary_service.get_summary(db, session_id)


def _safe_unlink_video(video_path: Optional[str]) -> None:
    if not video_path:
        return
    settings = get_settings()
    try:
        upload_root = Path(settings.upload_dir).resolve()
        path = Path(video_path)
        if not path.is_absolute():
            path = upload_root / path
        resolved = path.resolve()
        if upload_root in resolved.parents or resolved.parent == upload_root:
            if resolved.is_file():
                resolved.unlink()
                logger.info("Deleted session video %s", resolved)
            # Drop empty session folder
            parent = resolved.parent
            if parent.is_dir() and parent != upload_root and not any(parent.iterdir()):
                parent.rmdir()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not delete video %s: %s", video_path, type(exc).__name__)


def delete_session(db: Session, session_id: int) -> None:
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")

    video_path = row.video_path
    db.delete(row)  # cascades topics, modes, windows, events, pulse, jobs
    db.commit()

    invalidate_session_caches(session_id)
    _safe_unlink_video(video_path)
