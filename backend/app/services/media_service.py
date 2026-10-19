"""Stream uploads to UPLOAD_DIR, attach sources, purge video files."""

from __future__ import annotations

import logging
import re
import shutil
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.cache.keys import invalidate_session_caches
from app.core.exceptions import AppError, NotFoundError, PayloadTooLargeError
from app.core.settings import get_settings
from app.db.enums import SessionStatus, SourceType
from app.db.models import Session as SessionModel
from app.schemas.media import SourceUpdate, UploadResult
from app.schemas.sessions import SessionRead
from app.services.session_service import _to_read

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp4", ".webm"}
ALLOWED_CONTENT_TYPES = {
    "video/mp4",
    "video/webm",
    "application/octet-stream",
    "application/mp4",
}
CHUNK_SIZE = 1024 * 1024  # 1 MiB
_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def _upload_root() -> Path:
    root = Path(get_settings().upload_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_dir(session_id: int) -> Path:
    """Return UPLOAD_DIR/{session_id}/ — never accepts user path segments."""
    if session_id <= 0:
        raise AppError("Invalid session id", status_code=400, code="bad_session")
    path = (_upload_root() / str(session_id)).resolve()
    root = _upload_root()
    if root not in path.parents and path != root:
        raise AppError("Invalid upload path", status_code=400, code="bad_path")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ensure_under_upload(path: Path) -> Path:
    resolved = path.resolve()
    root = _upload_root()
    if root not in resolved.parents and resolved != root:
        raise AppError("Path escapes upload directory", status_code=400, code="bad_path")
    return resolved


def _safe_filename(name: Optional[str]) -> str:
    base = Path(name or "lecture.mp4").name
    base = _SAFE_NAME.sub("_", base).strip("._") or "lecture.mp4"
    if len(base) > 180:
        stem = Path(base).stem[:160]
        suf = Path(base).suffix[:20]
        base = f"{stem}{suf}"
    return base


def _get_session_row(db: Session, session_id: int) -> SessionModel:
    row = db.scalars(
        select(SessionModel)
        .options(joinedload(SessionModel.room_config))
        .where(SessionModel.id == session_id)
    ).unique().first()
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    return row


def _mark_ready_if_applicable(row: SessionModel) -> None:
    if row.status in (
        SessionStatus.DRAFT.value,
        SessionStatus.PURGED_VIDEO.value,
        SessionStatus.ERROR.value,
    ):
        row.status = SessionStatus.READY.value


def _relative_video_path(abs_path: Path) -> str:
    try:
        return abs_path.resolve().relative_to(_upload_root()).as_posix()
    except ValueError:
        return abs_path.name


def _safe_unlink(video_path: Optional[str]) -> None:
    if not video_path:
        return
    try:
        candidate = Path(video_path)
        if not candidate.is_absolute():
            candidate = _upload_root() / candidate
        resolved = _ensure_under_upload(candidate)
        if resolved.is_file():
            resolved.unlink()
            logger.info("Purged video %s", resolved)
        # Remove empty session folder
        parent = resolved.parent
        if parent.is_dir() and parent != _upload_root() and not any(parent.iterdir()):
            parent.rmdir()
    except AppError:
        logger.warning("Refused to purge path outside upload dir: %s", video_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not purge video %s: %s", video_path, type(exc).__name__)


def _refuse_if_analyzing(row) -> None:
    if row.status == SessionStatus.ANALYZING.value:
        raise AppError(
            "Cannot change media while analysis is running — wait for the job to finish or re-run to supersede",
            status_code=409,
            code="media_while_analyzing",
        )


def upload_video(
    db: Session,
    session_id: int,
    *,
    filename: Optional[str],
    content_type: Optional[str],
    fileobj: BinaryIO,
) -> Tuple[UploadResult, SessionRead]:
    settings = get_settings()
    max_bytes = int(settings.max_upload_mb) * 1024 * 1024

    row = _get_session_row(db, session_id)
    _refuse_if_analyzing(row)

    safe_name = _safe_filename(filename)
    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(
            "Only MP4 and WebM uploads are supported",
            status_code=400,
            code="unsupported_media_type",
            details={"allowed": sorted(ALLOWED_EXTENSIONS)},
        )
    if content_type and content_type.split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        # Soft check — extension is authoritative for browsers that send octet-stream
        if content_type.split(";")[0].strip().lower() not in ("", "*/*"):
            logger.info("Unusual content-type for upload: %s", content_type)

    dest_dir = _session_dir(session_id)
    dest = _ensure_under_upload(dest_dir / safe_name)

    # If same name exists, write to temp then replace
    tmp = dest.with_suffix(dest.suffix + ".partial")
    size = 0
    try:
        with tmp.open("wb") as out:
            while True:
                chunk = fileobj.read(CHUNK_SIZE)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    raise PayloadTooLargeError(
                        f"Upload exceeds MAX_UPLOAD_MB ({settings.max_upload_mb} MB)",
                        details={"max_upload_mb": settings.max_upload_mb},
                    )
                out.write(chunk)
        if size == 0:
            raise AppError("Empty upload", status_code=400, code="empty_upload")

        # Replace previous file for this session
        old_path = row.video_path
        tmp.replace(dest)
        if old_path:
            old = Path(old_path)
            if not old.is_absolute():
                old = _upload_root() / old
            try:
                old_resolved = _ensure_under_upload(old)
                if old_resolved != dest and old_resolved.is_file():
                    old_resolved.unlink()
            except AppError:
                pass

        rel = _relative_video_path(dest)
        row.video_path = rel
        row.source_type = SourceType.UPLOAD.value
        row.source_url = None  # file is the source of truth
        _mark_ready_if_applicable(row)
        db.commit()
        db.refresh(row)
        invalidate_session_caches(session_id)

        result = UploadResult(
            session_id=session_id,
            filename=safe_name,
            size_bytes=size,
            content_type=content_type,
            has_video=True,
            status=row.status,
            relative_path=rel,
        )
        return result, _to_read(_get_session_row(db, session_id))
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def set_source(db: Session, session_id: int, payload: SourceUpdate) -> SessionRead:
    row = _get_session_row(db, session_id)
    _refuse_if_analyzing(row)
    row.source_type = payload.source_type
    row.source_url = payload.source_url

    if payload.source_type == SourceType.UPLOAD.value:
        # Preference only — readiness still needs a file
        if not row.video_path:
            if row.status == SessionStatus.READY.value:
                row.status = SessionStatus.DRAFT.value
        else:
            _mark_ready_if_applicable(row)
    else:
        # Webcam / phone: URL or device hint is enough for ready
        if row.source_url:
            _mark_ready_if_applicable(row)

    db.commit()
    invalidate_session_caches(session_id)
    return _to_read(_get_session_row(db, session_id))


def purge_video(db: Session, session_id: int) -> SessionRead:
    row = _get_session_row(db, session_id)
    if row.status == SessionStatus.ANALYZING.value:
        raise AppError(
            "Cannot purge video while analysis is running — wait for the job to finish or re-run to supersede",
            status_code=409,
            code="purge_while_analyzing",
        )
    path = row.video_path
    row.video_path = None
    # Keep aggregates; mark purged if we had media or were ready/complete
    if row.status in (
        SessionStatus.READY.value,
        SessionStatus.COMPLETE.value,
        SessionStatus.DRAFT.value,
        SessionStatus.ERROR.value,
        SessionStatus.PURGED_VIDEO.value,
    ):
        # If still has webcam/phone source, stay ready; else purged_video
        if row.source_type in (
            SourceType.WEBCAM.value,
            SourceType.PHONE_RTSP.value,
        ) and row.source_url:
            row.status = SessionStatus.READY.value
        else:
            row.status = SessionStatus.PURGED_VIDEO.value

    db.commit()
    invalidate_session_caches(session_id)
    _safe_unlink(path)

    # Also clear any leftover files in session dir
    try:
        sdir = _upload_root() / str(session_id)
        if sdir.is_dir():
            shutil.rmtree(sdir, ignore_errors=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not rmtree session upload dir: %s", type(exc).__name__)

    return _to_read(_get_session_row(db, session_id))
