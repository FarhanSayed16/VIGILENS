"""Analysis job lifecycle: Redis lock, DB rows, real or fake worker thread."""

from __future__ import annotations

import logging
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.cache.keys import invalidate_session_caches
from app.cache.redis_client import (
    force_clear_analysis_lock,
    get_analysis_lock_holder,
    get_job_status_cache,
    release_analysis_lock,
    set_job_status_cache,
    try_acquire_analysis_lock,
)
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.core.settings import get_settings
from app.db.enums import JobStatus, SessionStatus, SourceType
from app.db.models import AnalysisJob, ModeChange, RoomConfig, Session as SessionModel, Topic
from app.db.session import SessionLocal
from app.schemas.jobs import AnalysisStartResponse, JobRead
from app.schemas.results import WorkerResultPayload
from app.services import result_service

logger = logging.getLogger(__name__)

# Ensure repo root on path so `worker.*` imports
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from worker.fake_worker import JobContract, estimate_duration_sec  # noqa: E402
from worker.jobs import run_fake_job, run_real_job  # noqa: E402


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_media_path(row: SessionModel) -> Optional[str]:
    if not row.video_path:
        return None
    settings = get_settings()
    path = Path(row.video_path)
    if not path.is_absolute():
        path = Path(settings.upload_dir) / path
    return str(path.resolve())


def _source_ready(row: SessionModel) -> bool:
    if row.source_type == SourceType.UPLOAD.value:
        path = _resolve_media_path(row)
        return bool(path and Path(path).is_file())
    if row.source_type in (SourceType.WEBCAM.value, SourceType.PHONE_RTSP.value):
        return bool(row.source_url)
    return False


def _to_job_read(job: AnalysisJob, *, stage: Optional[str] = None) -> JobRead:
    cached = get_job_status_cache(job.id) or {}
    st = stage or cached.get("stage")
    progress = float(cached.get("progress_pct", job.progress_pct))
    status = cached.get("status") or job.status
    # Prefer DB terminal states
    if job.status in (
        JobStatus.DONE.value,
        JobStatus.ERROR.value,
        JobStatus.CANCELLED.value,
    ):
        status = job.status
        progress = float(job.progress_pct)
    return JobRead(
        id=job.id,
        session_id=job.session_id,
        status=status,  # type: ignore[arg-type]
        progress_pct=progress,
        stage=st,  # type: ignore[arg-type]
        error_message=job.error_message or cached.get("error_message"),
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


def get_job(db: Session, job_id: int) -> JobRead:
    job = db.get(AnalysisJob, job_id)
    if job is None:
        raise NotFoundError(f"Job {job_id} not found")
    return _to_job_read(job)


def _supersede_unfinished(db: Session, session_id: int) -> List[int]:
    rows = db.scalars(
        select(AnalysisJob).where(
            AnalysisJob.session_id == session_id,
            AnalysisJob.status.in_(
                [JobStatus.QUEUED.value, JobStatus.RUNNING.value]
            ),
        )
    ).all()
    cancelled_ids: List[int] = []
    for job in rows:
        job.status = JobStatus.CANCELLED.value
        job.finished_at = _utcnow()
        job.error_message = "Superseded by a newer analysis run"
        cancelled_ids.append(job.id)
        set_job_status_cache(
            job.id,
            {
                "session_id": session_id,
                "status": JobStatus.CANCELLED.value,
                "progress_pct": job.progress_pct,
                "stage": "cancelled",
                "error_message": job.error_message,
            },
        )
        holder = get_analysis_lock_holder()
        if holder == job.id:
            release_analysis_lock(job.id)
    if cancelled_ids:
        db.flush()
        logger.info(
            "Superseded unfinished jobs for session %s: %s",
            session_id,
            cancelled_ids,
        )
    return cancelled_ids


def _publish(job_id: int, session_id: int, status: str, progress: float, stage: str, error: Optional[str] = None) -> None:
    set_job_status_cache(
        job_id,
        {
            "session_id": session_id,
            "status": status,
            "progress_pct": progress,
            "stage": stage,
            "error_message": error,
        },
    )


def start_analysis(db: Session, session_id: int) -> AnalysisStartResponse:
    # Redis must be up for lock + progress
    from app.cache.redis_client import get_redis

    _r = get_redis()
    try:
        _r.ping()
    finally:
        _r.close()

    row = db.scalars(
        select(SessionModel)
        .options(joinedload(SessionModel.room_config))
        .where(SessionModel.id == session_id)
    ).unique().first()
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")

    if row.room_config is None:
        raise AppError("Session has no room config", status_code=400, code="no_room")

    if not _source_ready(row):
        raise AppError(
            "Source not ready — upload a video or set webcam/phone source first",
            status_code=400,
            code="source_not_ready",
            details={"source_type": row.source_type, "has_video": bool(row.video_path)},
        )

    # Global lock check before creating job
    holder = get_analysis_lock_holder()
    if holder is not None:
        holder_job = db.get(AnalysisJob, holder)
        if holder_job is None or holder_job.status in (
            JobStatus.DONE.value,
            JobStatus.ERROR.value,
            JobStatus.CANCELLED.value,
        ):
            force_clear_analysis_lock()
        elif holder_job.session_id != session_id:
            raise ConflictError(
                "Another analysis job is already running on this machine",
                details={"lock_holder_job_id": holder, "holder_session_id": holder_job.session_id},
            )
        # Same session unfinished → supersede will release

    _supersede_unfinished(db, session_id)

    job = AnalysisJob(
        session_id=session_id,
        status=JobStatus.QUEUED.value,
        progress_pct=0.0,
    )
    db.add(job)
    row.status = SessionStatus.ANALYZING.value
    db.flush()

    if not try_acquire_analysis_lock(job.id):
        # Race: another session grabbed lock
        holder = get_analysis_lock_holder()
        job.status = JobStatus.CANCELLED.value
        job.error_message = "Could not acquire analysis lock"
        job.finished_at = _utcnow()
        row.status = SessionStatus.READY.value
        db.commit()
        raise ConflictError(
            "Another analysis job is already running on this machine",
            details={"lock_holder_job_id": holder},
        )

    db.commit()
    db.refresh(job)
    invalidate_session_caches(session_id)
    _publish(job.id, session_id, JobStatus.QUEUED.value, 0.0, "queued")

    thread = threading.Thread(
        target=_run_job_thread,
        args=(job.id, session_id),
        name=f"vigilens-job-{job.id}",
        daemon=True,
    )
    thread.start()
    logger.info("Started analysis job_id=%s session_id=%s", job.id, session_id)

    read = _to_job_read(job, stage="queued")
    return AnalysisStartResponse(**read.model_dump())


def _run_job_thread(job_id: int, session_id: int) -> None:
    db = SessionLocal()
    try:
        _execute_job(db, job_id, session_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Job %s crashed: %s", job_id, exc)
        try:
            job = db.get(AnalysisJob, job_id)
            sess = db.get(SessionModel, session_id)
            if job and job.status not in (JobStatus.DONE.value, JobStatus.CANCELLED.value):
                job.status = JobStatus.ERROR.value
                job.error_message = str(exc)[:2000]
                job.finished_at = _utcnow()
                job.progress_pct = float(job.progress_pct or 0)
            if sess and sess.status == SessionStatus.ANALYZING.value:
                sess.status = SessionStatus.ERROR.value
            db.commit()
            _publish(
                job_id,
                session_id,
                JobStatus.ERROR.value,
                0.0,
                "error",
                str(exc)[:500],
            )
        except Exception:  # noqa: BLE001
            db.rollback()
        finally:
            release_analysis_lock(job_id)
    finally:
        db.close()


def _execute_job(db: Session, job_id: int, session_id: int) -> None:
    job = db.get(AnalysisJob, job_id)
    session = db.scalars(
        select(SessionModel)
        .options(joinedload(SessionModel.room_config))
        .where(SessionModel.id == session_id)
    ).unique().first()
    if job is None or session is None:
        release_analysis_lock(job_id)
        return

    # Bail if superseded before start
    if job.status == JobStatus.CANCELLED.value:
        release_analysis_lock(job_id)
        return

    job.status = JobStatus.RUNNING.value
    job.progress_pct = 5.0
    db.commit()
    _publish(job_id, session_id, JobStatus.RUNNING.value, 5.0, "ingest")
    time.sleep(0.35)

    # Re-check cancel
    db.refresh(job)
    if job.status == JobStatus.CANCELLED.value:
        release_analysis_lock(job_id)
        return

    room: Optional[RoomConfig] = session.room_config
    seat_count = 12
    if room and isinstance(room.seat_regions_json, list):
        seat_count = max(1, len(room.seat_regions_json))

    topics = [
        {
            "id": t.id,
            "start_sec": t.start_sec,
            "end_sec": t.end_sec,
            "label": t.label,
        }
        for t in db.scalars(
            select(Topic).where(Topic.session_id == session_id).order_by(Topic.start_sec)
        ).all()
    ]
    modes = [
        {"start_sec": m.start_sec, "mode": m.mode}
        for m in db.scalars(
            select(ModeChange)
            .where(ModeChange.session_id == session_id)
            .order_by(ModeChange.start_sec)
        ).all()
    ]

    media = _resolve_media_path(session)
    settings = get_settings()
    duration = estimate_duration_sec(video_path=media, topics=topics)
    # Prefer OpenCV probe duration when available (real worker)
    if media and not settings.use_fake_worker:
        try:
            from worker import capture as worker_capture

            info = worker_capture.probe_source(media, config_path=settings.config_path)
            if info.frame_count and info.fps_native > 1e-3:
                duration = max(30.0, info.frame_count / info.fps_native)
        except Exception as exc:  # noqa: BLE001
            logger.debug("duration probe fallback: %s", type(exc).__name__)

    def _job_is_active() -> bool:
        """Fresh DB read — avoid identity-map stale RUNNING after supersede."""
        try:
            db.expire_all()
            j = db.get(AnalysisJob, job_id)
            if j is None:
                return False
            return j.status in (
                JobStatus.QUEUED.value,
                JobStatus.RUNNING.value,
            )
        except Exception:  # noqa: BLE001
            return False

    def on_progress(pct: float, stage: str) -> None:
        # Soft update — must not resurrect CANCELLED/DONE after supersede
        try:
            db.expire_all()
            j = db.get(AnalysisJob, job_id)
            if j is None:
                return
            if j.status not in (
                JobStatus.QUEUED.value,
                JobStatus.RUNNING.value,
            ):
                return
            j.progress_pct = float(pct)
            if j.status == JobStatus.QUEUED.value:
                j.status = JobStatus.RUNNING.value
            db.commit()
            _publish(job_id, session_id, JobStatus.RUNNING.value, float(pct), stage)
        except Exception as exc:  # noqa: BLE001
            logger.debug("progress update failed: %s", type(exc).__name__)
            db.rollback()

    on_progress(10.0, "ingest")

    if not _job_is_active():
        release_analysis_lock(job_id)
        return

    seat_regions = None
    if room and isinstance(room.seat_regions_json, list):
        seat_regions = room.seat_regions_json

    contract = JobContract(
        session_id=session_id,
        job_id=job_id,
        source_type=session.source_type,
        video_path=media,
        source_url=session.source_url,
        seat_count=seat_count,
        seat_regions=seat_regions,
        target_roi=room.target_roi_json if room else None,
        topics=topics,
        modes=modes,
        duration_sec=duration,
    )

    if settings.use_fake_worker:
        logger.info("Job %s using FAKE worker (USE_FAKE_WORKER=true)", job_id)
        raw = run_fake_job(contract, on_progress=on_progress)
    else:
        logger.info("Job %s using REAL worker (YOLO/MediaPipe)", job_id)
        raw = run_real_job(
            contract,
            on_progress=on_progress,
            config_path=settings.config_path,
            max_frames=settings.worker_max_frames,
        )

    if not _job_is_active():
        release_analysis_lock(job_id)
        return

    # Another job may have taken the global lock after supersede
    holder = get_analysis_lock_holder()
    if holder is not None and holder != job_id:
        logger.warning(
            "Job %s lost analysis lock to job %s — skipping persist",
            job_id,
            holder,
        )
        return

    on_progress(90.0, "aggregate")
    if not _job_is_active():
        release_analysis_lock(job_id)
        return

    payload = WorkerResultPayload.model_validate(raw)
    summary = result_service.persist_and_warm(db, session_id, payload)

    # refresh objects after commit in persist
    db.expire_all()
    job = db.get(AnalysisJob, job_id)
    session = db.get(SessionModel, session_id)
    assert job is not None and session is not None

    if job.status not in (
        JobStatus.QUEUED.value,
        JobStatus.RUNNING.value,
    ):
        release_analysis_lock(job_id)
        return

    holder = get_analysis_lock_holder()
    if holder is not None and holder != job_id:
        logger.warning(
            "Job %s lost lock before DONE — not marking complete", job_id
        )
        return

    job.status = JobStatus.DONE.value
    job.progress_pct = 100.0
    job.finished_at = _utcnow()
    job.error_message = None
    session.status = SessionStatus.COMPLETE.value
    db.commit()
    _publish(job_id, session_id, JobStatus.DONE.value, 100.0, "done")
    release_analysis_lock(job_id)

    # Privacy default: purge raw video after successful analysis (aggregates kept)
    try:
        from app.services.retention_service import maybe_purge_video_after_analysis

        maybe_purge_video_after_analysis(db, session_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Post-analysis retention hook failed: %s", type(exc).__name__)

    logger.info(
        "Job %s done session=%s windows=%s events=%s mean_ttoi=%s",
        job_id,
        session_id,
        summary.get("window_count"),
        summary.get("event_count"),
        summary.get("mean_ttoi"),
    )
