"""Live lecture Start/Stop control plane (Phase 26–29)."""

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
    clear_live_stop,
    force_clear_analysis_lock,
    get_analysis_lock_holder,
    get_live_preview_jpeg,
    get_live_snapshot,
    set_live_preview_jpeg,
    live_stop_requested,
    refresh_analysis_lock,
    release_analysis_lock,
    request_live_stop,
    set_job_status_cache,
    set_live_snapshot,
    try_acquire_analysis_lock,
)
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.core.settings import get_settings
from app.db.enums import JobStatus, SessionStatus, SourceType
from app.db.models import AnalysisJob, ModeChange, Session as SessionModel, Topic
from app.db.session import SessionLocal
from app.schemas.live import LiveAlert, LiveGroup, LiveSeatStat, LiveState
from app.schemas.results import EventPayload, WindowPayload
from app.services import result_service

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from worker.drop_events import detect_declines  # noqa: E402
from worker.fake_worker import JobContract, estimate_duration_sec  # noqa: E402
from worker.groups import groups_to_events  # noqa: E402
from worker.live_session import run_fake_live_session, run_real_live_session  # noqa: E402


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _source_ready(row: SessionModel) -> bool:
    if row.source_type == SourceType.UPLOAD.value:
        if not row.video_path:
            return False
        settings = get_settings()
        path = Path(row.video_path)
        if not path.is_absolute():
            path = Path(settings.upload_dir) / path
        return path.is_file()
    return bool(row.source_url)


def _resolve_media(row: SessionModel) -> Optional[str]:
    if not row.video_path:
        return None
    settings = get_settings()
    path = Path(row.video_path)
    if not path.is_absolute():
        path = Path(settings.upload_dir) / path
    return str(path.resolve())


def _publish(job_id: int, session_id: int, status: str, progress: float, stage: str) -> None:
    set_job_status_cache(
        job_id,
        {
            "job_id": job_id,
            "session_id": session_id,
            "status": status,
            "progress_pct": progress,
            "stage": stage,
        },
    )


def _empty_state(row: SessionModel, *, message: Optional[str] = None) -> LiveState:
    snap = get_live_snapshot(row.id) or {}
    running = row.status == SessionStatus.LIVE.value
    # Always wall-clock from session start — never Redis window cadence
    elapsed = 0.0
    if row.started_at:
        end = row.ended_at or _utcnow()
        started = row.started_at
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        elapsed = max(0.0, (end - started).total_seconds())
    window_sec = float(snap.get("window_seconds") or 30.0)
    next_in = None
    if running and window_sec > 0:
        next_in = max(0.0, window_sec - (elapsed % window_sec))
    return LiveState(
        session_id=row.id,
        status=row.status,
        running=running,
        job_id=snap.get("job_id"),
        elapsed_sec=elapsed,
        window_seconds=window_sec,
        next_window_in_sec=next_in,
        ttoi=snap.get("ttoi"),
        coverage_pct=snap.get("coverage_pct"),
        usable_seats=snap.get("usable_seats"),
        expected_seats=snap.get("expected_seats"),
        persons_detected=snap.get("persons_detected"),
        persons_in_seats=snap.get("persons_in_seats"),
        per_seat=[LiveSeatStat(**s) for s in snap.get("per_seat") or []],
        groups=[LiveGroup(**g) for g in snap.get("groups") or []],
        alerts=[LiveAlert(**a) for a in snap.get("alerts") or []],
        updated_at=snap.get("updated_at"),
        secondary_source_url=row.secondary_source_url,
        message=message or snap.get("message"),
        detection_hint=snap.get("detection_hint"),
        preview_available=bool(
            snap.get("preview_available") or get_live_preview_jpeg(row.id)
        ),
    )


def get_preview_jpeg(db: Session, session_id: int) -> Optional[bytes]:
    """Latest worker JPEG for Console (auth checked by caller)."""
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    return get_live_preview_jpeg(session_id)


def get_live_state(db: Session, session_id: int) -> LiveState:
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    return _empty_state(row)


def set_secondary_source(
    db: Session, session_id: int, secondary_source_url: Optional[str]
) -> LiveState:
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    row.secondary_source_url = (secondary_source_url or "").strip() or None
    db.commit()
    db.refresh(row)
    return _empty_state(row)


def _job_is_terminal(job: Optional[AnalysisJob]) -> bool:
    if job is None:
        return True
    return job.status in (
        JobStatus.DONE.value,
        JobStatus.ERROR.value,
        JobStatus.CANCELLED.value,
    )


def _snapshot_stale(session_id: int, *, max_age_sec: float = 90.0) -> bool:
    snap = get_live_snapshot(session_id) or {}
    raw = snap.get("updated_at")
    if not raw:
        return True
    try:
        ts = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (_utcnow() - ts).total_seconds()
        return age > max_age_sec
    except Exception:  # noqa: BLE001
        return True


def _reclaim_stale_analysis_lock(db: Session, session_id: int) -> None:
    """
    Drop Redis lock (and stuck LIVE sessions) when the holder is dead/stale.

    Prevents permanent 409 after a crashed worker or abandoned tab.
    """
    holder = get_analysis_lock_holder()
    if holder is None:
        return
    hj = db.get(AnalysisJob, holder)
    if _job_is_terminal(hj):
        force_clear_analysis_lock()
        return
    assert hj is not None
    other_id = int(hj.session_id)
    other = db.get(SessionModel, other_id)
    other_live = other is not None and other.status == SessionStatus.LIVE.value
    stale = (not other_live) or _snapshot_stale(other_id)
    if other_id == session_id or stale:
        logger.warning(
            "Reclaiming analysis lock job_id=%s session_id=%s stale=%s",
            holder,
            other_id,
            stale,
        )
        request_live_stop(other_id)
        hj.status = JobStatus.CANCELLED.value
        hj.finished_at = _utcnow()
        hj.error_message = (hj.error_message or "")[:500] + " | lock reclaimed"
        if other is not None and other.status == SessionStatus.LIVE.value:
            other.status = (
                SessionStatus.READY.value
                if _source_ready(other)
                else SessionStatus.DRAFT.value
            )
            other.ended_at = _utcnow()
        force_clear_analysis_lock()
        db.commit()
        return
    # Healthy live on another session — genuine conflict
    raise ConflictError(
        f"Session {other_id} is still live — Stop that lecture first "
        f"(or wait ~90s if it crashed).",
        details={"lock_holder_job_id": holder, "lock_holder_session_id": other_id},
    )


def start_live(db: Session, session_id: int) -> LiveState:
    row = db.scalars(
        select(SessionModel)
        .options(joinedload(SessionModel.room_config))
        .where(SessionModel.id == session_id)
    ).unique().first()
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    # Stuck LIVE with dead worker → reclaim then continue Start
    if row.status == SessionStatus.LIVE.value:
        snap_ok = not _snapshot_stale(session_id, max_age_sec=45.0)
        holder = get_analysis_lock_holder()
        holder_job = db.get(AnalysisJob, holder) if holder is not None else None
        owns = (
            holder_job is not None
            and holder_job.session_id == session_id
            and not _job_is_terminal(holder_job)
        )
        if snap_ok and owns:
            return _empty_state(row, message="Lecture already live")
        logger.warning("Recovering stuck LIVE session_id=%s", session_id)
        request_live_stop(session_id)
        for j in db.scalars(
            select(AnalysisJob).where(
                AnalysisJob.session_id == session_id,
                AnalysisJob.status.in_(
                    [JobStatus.QUEUED.value, JobStatus.RUNNING.value]
                ),
            )
        ).all():
            j.status = JobStatus.CANCELLED.value
            j.finished_at = _utcnow()
            j.error_message = "Recovered stuck live session"
        row.status = (
            SessionStatus.READY.value if _source_ready(row) else SessionStatus.DRAFT.value
        )
        row.ended_at = _utcnow()
        if owns or holder is not None:
            force_clear_analysis_lock()
        db.commit()
        db.refresh(row)

    if not _source_ready(row):
        raise AppError(
            "Source not ready — set webcam/upload before Start lecture",
            status_code=400,
            code="source_not_ready",
        )
    if not row.room_config or not row.room_config.seat_regions_json:
        raise AppError(
            "Room has no seat regions — calibrate in Rooms first",
            status_code=400,
            code="no_seats",
        )

    _reclaim_stale_analysis_lock(db, session_id)
    db.refresh(row)

    # Cancel unfinished jobs for this session
    for j in db.scalars(
        select(AnalysisJob).where(
            AnalysisJob.session_id == session_id,
            AnalysisJob.status.in_(
                [JobStatus.QUEUED.value, JobStatus.RUNNING.value]
            ),
        )
    ).all():
        j.status = JobStatus.CANCELLED.value
        j.finished_at = _utcnow()
        j.error_message = "Superseded by live start"

    result_service.clear_session_results(db, session_id)
    clear_live_stop(session_id)

    job = AnalysisJob(
        session_id=session_id,
        status=JobStatus.QUEUED.value,
        progress_pct=0.0,
    )
    db.add(job)
    row.status = SessionStatus.LIVE.value
    row.started_at = _utcnow()
    row.ended_at = None
    db.flush()

    if not try_acquire_analysis_lock(job.id):
        job.status = JobStatus.CANCELLED.value
        job.finished_at = _utcnow()
        row.status = SessionStatus.READY.value if _source_ready(row) else SessionStatus.DRAFT.value
        db.commit()
        raise ConflictError("Could not acquire analysis lock for live lecture")

    db.commit()
    db.refresh(job)
    invalidate_session_caches(session_id)
    _publish(job.id, session_id, JobStatus.QUEUED.value, 0.0, "queued")
    set_live_snapshot(
        session_id,
        {
            "job_id": job.id,
            "ttoi": None,
            "coverage_pct": None,
            "per_seat": [],
            "groups": [],
            "alerts": [],
            "elapsed_sec": 0.0,
            "updated_at": _utcnow().isoformat(),
            "message": "Starting live capture…",
        },
    )

    thread = threading.Thread(
        target=_run_live_thread,
        args=(job.id, session_id),
        name=f"vigilens-live-{job.id}",
        daemon=True,
    )
    thread.start()
    logger.info("Started live lecture job_id=%s session_id=%s", job.id, session_id)
    db.refresh(row)
    return _empty_state(row, message="Live lecture started")


def stop_live(db: Session, session_id: int) -> LiveState:
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    request_live_stop(session_id)
    # Soft mark — worker finalizes status
    snap = get_live_snapshot(session_id) or {}
    snap["message"] = "Stop requested — finalizing…"
    snap["updated_at"] = _utcnow().isoformat()
    set_live_snapshot(session_id, snap)
    # Wait briefly for worker to finish
    for _ in range(40):
        db.expire_all()
        row = db.get(SessionModel, session_id)
        if row and row.status != SessionStatus.LIVE.value:
            break
        time.sleep(0.25)
    db.expire_all()
    row = db.get(SessionModel, session_id)
    assert row is not None
    # If worker hung, force session + lock free so Start works again
    if row.status == SessionStatus.LIVE.value:
        for j in db.scalars(
            select(AnalysisJob).where(
                AnalysisJob.session_id == session_id,
                AnalysisJob.status.in_(
                    [JobStatus.QUEUED.value, JobStatus.RUNNING.value]
                ),
            )
        ).all():
            j.status = JobStatus.CANCELLED.value
            j.finished_at = _utcnow()
            j.error_message = "Stopped (worker did not finalize in time)"
        row.status = (
            SessionStatus.COMPLETE.value
            if (snap.get("ttoi") is not None or snap.get("per_seat"))
            else (
                SessionStatus.READY.value
                if _source_ready(row)
                else SessionStatus.DRAFT.value
            )
        )
        row.ended_at = _utcnow()
        db.commit()
        db.refresh(row)
    holder = get_analysis_lock_holder()
    if holder is not None:
        hj = db.get(AnalysisJob, holder)
        if hj is None or hj.session_id == session_id or _job_is_terminal(hj):
            force_clear_analysis_lock()
    return _empty_state(row, message="Lecture stopped")


def set_event_feedback(
    db: Session, session_id: int, event_id: int, feedback: str
) -> Dict[str, Any]:
    row = result_service.set_event_feedback(db, session_id, event_id, feedback)
    return {"id": row.id, "lecturer_feedback": row.lecturer_feedback}


def _run_live_thread(job_id: int, session_id: int) -> None:
    db = SessionLocal()
    try:
        _execute_live(db, job_id, session_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Live job %s crashed: %s", job_id, exc)
        try:
            job = db.get(AnalysisJob, job_id)
            sess = db.get(SessionModel, session_id)
            if job and job.status not in (JobStatus.DONE.value, JobStatus.CANCELLED.value):
                job.status = JobStatus.ERROR.value
                job.error_message = str(exc)[:2000]
                job.finished_at = _utcnow()
            if sess and sess.status == SessionStatus.LIVE.value:
                sess.status = SessionStatus.ERROR.value
                sess.ended_at = _utcnow()
            db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
        finally:
            release_analysis_lock(job_id)
            request_live_stop(session_id)
    finally:
        db.close()


def _execute_live(db: Session, job_id: int, session_id: int) -> None:
    job = db.get(AnalysisJob, job_id)
    session = db.scalars(
        select(SessionModel)
        .options(joinedload(SessionModel.room_config))
        .where(SessionModel.id == session_id)
    ).unique().first()
    if job is None or session is None:
        release_analysis_lock(job_id)
        return

    job.status = JobStatus.RUNNING.value
    job.progress_pct = 5.0
    db.commit()
    _publish(job_id, session_id, JobStatus.RUNNING.value, 5.0, "ingest")

    room = session.room_config
    seat_regions = room.seat_regions_json if room else []
    seat_count = max(1, len(seat_regions) if isinstance(seat_regions, list) else 8)
    topics = [
        {"id": t.id, "start_sec": t.start_sec, "end_sec": t.end_sec, "label": t.label}
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
    media = _resolve_media(session)
    facing_mode = None
    if room and isinstance(room.camera_defaults, dict):
        facing_mode = room.camera_defaults.get("facing_mode")
        if not facing_mode and room.camera_defaults.get("placement") == "facing_class":
            facing_mode = "toward_camera"

    duration = estimate_duration_sec(video_path=media, topics=topics)
    if not media:
        # Webcam: allow long run until stop (fake uses compressed ticks)
        duration = 3600.0

    contract = JobContract(
        session_id=session_id,
        job_id=job_id,
        source_type=session.source_type,
        video_path=media,
        source_url=session.source_url,
        seat_count=seat_count,
        seat_regions=seat_regions if isinstance(seat_regions, list) else None,
        target_roi=room.target_roi_json if room else None,
        facing_mode=str(facing_mode) if facing_mode else None,
        topics=topics,
        modes=modes,
        duration_sec=duration,
    )

    settings = get_settings()
    window_sec = 30.0
    alerts: List[Dict[str, Any]] = []
    last_groups: List[Dict[str, Any]] = []
    t0 = time.monotonic()

    def should_stop() -> bool:
        if live_stop_requested(session_id):
            return True
        try:
            db.expire_all()
            j = db.get(AnalysisJob, job_id)
            return j is None or j.status == JobStatus.CANCELLED.value
        except Exception:  # noqa: BLE001
            return True

    def on_progress(pct: float, stage: str) -> None:
        try:
            db.expire_all()
            j = db.get(AnalysisJob, job_id)
            if j is None or j.status not in (
                JobStatus.QUEUED.value,
                JobStatus.RUNNING.value,
            ):
                return
            j.progress_pct = float(pct)
            j.status = JobStatus.RUNNING.value
            db.commit()
            refresh_analysis_lock(job_id)
            _publish(job_id, session_id, JobStatus.RUNNING.value, float(pct), stage)
        except Exception:  # noqa: BLE001
            db.rollback()

    def on_heartbeat(hb: Dict[str, Any]) -> None:
        prev = get_live_snapshot(session_id) or {}
        prev.update(
            {
                "job_id": job_id,
                "window_seconds": window_sec,
                "persons_detected": hb.get("persons_detected"),
                "persons_in_seats": hb.get("persons_in_seats"),
                "detection_hint": hb.get("detection_hint"),
                "frame_luma": hb.get("frame_luma"),
                "worker_source": hb.get("worker_source") or prev.get("worker_source"),
                "updated_at": _utcnow().isoformat(),
                "message": hb.get("detection_hint") or prev.get("message"),
            }
        )
        set_live_snapshot(session_id, prev)

    def on_preview(jpeg: bytes) -> None:
        set_live_preview_jpeg(session_id, jpeg)
        prev = get_live_snapshot(session_id) or {}
        prev["preview_available"] = True
        prev["updated_at"] = _utcnow().isoformat()
        set_live_snapshot(session_id, prev)

    def on_window(
        w: Dict[str, Any],
        per_seat: List[Dict[str, Any]],
        groups: List[Dict[str, Any]],
    ) -> None:
        nonlocal last_groups, alerts
        last_groups = groups
        try:
            payload = WindowPayload.model_validate(w)
            result_service.append_window(db, session_id, payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("append_window failed: %s", type(exc).__name__)
            db.rollback()

        if w.get("candidate_decline") or (w.get("ttoi") is not None and float(w["ttoi"]) < 60):
            alerts.append(
                {
                    "kind": "orientation_decline",
                    "start_sec": w["start_sec"],
                    "end_sec": w["end_sec"],
                    "message": f"Class TTOI {w.get('ttoi')} in window",
                }
            )
        for g in groups:
            alerts.append(
                {
                    "kind": g.get("kind") or "decline_cluster",
                    "start_sec": w["start_sec"],
                    "end_sec": w["end_sec"],
                    "message": f"{g.get('label')} low orientation",
                    "group_label": g.get("label"),
                    "seat_ids": g.get("seat_ids") or [],
                }
            )
        # Keep feed short
        alerts = alerts[-20:]
        prev = get_live_snapshot(session_id) or {}
        set_live_snapshot(
            session_id,
            {
                **prev,
                "job_id": job_id,
                "window_seconds": window_sec,
                "ttoi": w.get("ttoi"),
                "coverage_pct": w.get("coverage_pct"),
                "usable_seats": w.get("usable_regions"),
                "expected_seats": w.get("expected_regions"),
                "per_seat": per_seat,
                "groups": groups,
                "alerts": alerts,
                "updated_at": _utcnow().isoformat(),
                "message": "Live — 30s window committed",
                "detection_hint": prev.get("detection_hint"),
            },
        )

    if settings.use_fake_worker:
        raw = run_fake_live_session(
            contract,
            window_seconds=window_sec,
            should_stop=should_stop,
            on_progress=on_progress,
            on_window=on_window,
            on_heartbeat=on_heartbeat,
            tick_seconds=1.5,
        )
    else:
        raw = run_real_live_session(
            contract,
            window_seconds=window_sec,
            should_stop=should_stop,
            on_progress=on_progress,
            on_window=on_window,
            on_heartbeat=on_heartbeat,
            on_preview=on_preview,
            config_path=settings.config_path,
        )

    # Finalize events from committed windows
    db.expire_all()
    from app.db.models import Window

    win_rows = db.scalars(
        select(Window)
        .where(Window.session_id == session_id)
        .order_by(Window.start_sec.asc())
    ).all()
    win_dicts = [
        {
            "start_sec": r.start_sec,
            "end_sec": r.end_sec,
            "ttoi": r.ttoi,
            "coverage_pct": r.coverage_pct,
            "candidate_decline": r.candidate_decline,
            "topic_id": r.topic_id,
            "teaching_mode": r.teaching_mode,
            "dominant_cue": r.dominant_cue,
            "data_quality_note": r.data_quality_note,
        }
        for r in win_rows
    ]
    try:
        events_raw = detect_declines(win_dicts, min_usable_seats=1)
        for i, row in enumerate(win_rows):
            if i < len(win_dicts):
                row.candidate_decline = bool(win_dicts[i].get("candidate_decline"))
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.debug("detect_declines soft-fail: %s", type(exc).__name__)
        events_raw = []

    event_payloads: List[EventPayload] = []
    for e in events_raw:
        if isinstance(e, dict):
            event_payloads.append(
                EventPayload(
                    start_sec=float(e["start_sec"]),
                    end_sec=float(e["end_sec"]),
                    depth=float(e.get("depth") or 10),
                    coverage_pct=e.get("coverage_pct"),
                    topic_id=e.get("topic_id"),
                    teaching_mode=e.get("teaching_mode"),
                    dominant_cue=e.get("dominant_cue"),
                    note=e.get("note") or "Candidate orientation decline",
                    kind="orientation_decline",
                )
            )

    # Group events from last snapshot clusters spanning last window
    if last_groups and win_rows:
        last = win_rows[-1]
        for ge in groups_to_events(
            last_groups,
            start_sec=last.start_sec,
            end_sec=last.end_sec,
            coverage_pct=last.coverage_pct,
        ):
            event_payloads.append(EventPayload.model_validate(ge))

    result_service.replace_events_only(db, session_id, event_payloads)

    db.expire_all()
    job = db.get(AnalysisJob, job_id)
    session = db.get(SessionModel, session_id)
    assert job is not None and session is not None
    job.status = JobStatus.DONE.value
    job.progress_pct = 100.0
    job.finished_at = _utcnow()
    session.status = SessionStatus.COMPLETE.value
    session.ended_at = _utcnow()
    db.commit()
    _publish(job_id, session_id, JobStatus.DONE.value, 100.0, "done")
    release_analysis_lock(job_id)
    clear_live_stop(session_id)
    set_live_snapshot(
        session_id,
        {
            "job_id": job_id,
            "ttoi": (get_live_snapshot(session_id) or {}).get("ttoi"),
            "coverage_pct": (get_live_snapshot(session_id) or {}).get("coverage_pct"),
            "per_seat": (get_live_snapshot(session_id) or {}).get("per_seat") or [],
            "groups": last_groups,
            "alerts": alerts,
            "elapsed_sec": time.monotonic() - t0,
            "updated_at": _utcnow().isoformat(),
            "message": "Lecture complete — open Review",
        },
    )
    logger.info(
        "Live lecture done job=%s session=%s windows=%s events=%s",
        job_id,
        session_id,
        len(win_rows),
        len(event_payloads),
    )
