"""
Streaming live lecture runner (Phase 27).

Captures until should_stop(), commits class + per-seat stats every window_seconds.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from worker.face_registrar import FaceSeatRegistrar
from worker.fake_worker import JobContract
from worker.groups import cluster_low_orientation_seats

logger = logging.getLogger(__name__)

ProgressCb = Callable[[float, str], None]
WindowCb = Callable[[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]], None]
HeartbeatCb = Callable[[Dict[str, Any]], None]
PreviewCb = Callable[[bytes], None]
StopFn = Callable[[], bool]


def _seat_ids_from_regions(regions: Optional[Sequence[Any]], seat_count: int) -> List[str]:
    ids: List[str] = []
    if regions:
        for i, r in enumerate(regions):
            if isinstance(r, dict) and r.get("id") is not None:
                ids.append(str(r["id"]))
            else:
                ids.append(f"seat_{i + 1}")
    if not ids:
        ids = [f"seat_{i}" for i in range(1, max(1, seat_count) + 1)]
    return ids


def run_fake_live_session(
    contract: JobContract,
    *,
    window_seconds: float = 30.0,
    should_stop: Optional[StopFn] = None,
    on_progress: Optional[ProgressCb] = None,
    on_window: Optional[WindowCb] = None,
    on_heartbeat: Optional[HeartbeatCb] = None,
    tick_seconds: float = 2.0,
) -> Dict[str, Any]:
    """Synthetic live stream with compressed window ticks until stop."""
    seat_ids = _seat_ids_from_regions(contract.seat_regions, contract.seat_count or 8)
    n_target = max(2, int(float(contract.duration_sec or 120) / max(1.0, window_seconds)))
    windows_out: List[Dict[str, Any]] = []
    t0 = time.monotonic()

    for i in range(n_target):
        if should_stop and should_stop():
            break
        start = i * window_seconds
        end = start + window_seconds
        base = 78.0 - (12.0 if n_target // 3 <= i < n_target // 3 + 2 else 0.0)
        per_seat: List[Dict[str, Any]] = []
        for j, sid in enumerate(seat_ids):
            o = base - (
                35.0 if j < 3 and n_target // 3 <= i < n_target // 3 + 2 else 0.0
            )
            o = max(10.0, min(95.0, o + (j % 3) * 2))
            per_seat.append(
                {"seat_id": sid, "orientation_pct": round(o, 1), "usable": True}
            )
        if on_heartbeat:
            on_heartbeat(
                {
                    "persons_detected": len(seat_ids),
                    "persons_in_seats": len(seat_ids),
                    "time_sec": start + tick_seconds,
                    "detection_hint": "Fake worker — synthetic detections",
                }
            )
        usable = len(per_seat)
        ttoi = round(sum(s["orientation_pct"] for s in per_seat) / usable, 1)
        w = {
            "start_sec": float(start),
            "end_sec": float(end),
            "topic_id": None,
            "teaching_mode": "explanation",
            "expected_regions": len(seat_ids),
            "usable_regions": usable,
            "coverage_pct": 100.0,
            "ttoi": ttoi,
            "ttoi_lo": max(0.0, ttoi - 5),
            "ttoi_hi": min(100.0, ttoi + 5),
            "head_down_cue_pct": 10.0,
            "hand_raise_events": 0,
            "candidate_decline": ttoi < 65,
            "dominant_cue": "target_oriented" if ttoi >= 65 else "yaw_away",
            "data_quality_note": None,
            "seat_stats": per_seat,
        }
        groups = cluster_low_orientation_seats(per_seat)
        windows_out.append(w)
        if on_window:
            on_window(w, per_seat, groups)
        if on_progress:
            on_progress(min(95.0, 10.0 + 80.0 * (i + 1) / n_target), "vision")
        time.sleep(max(0.05, tick_seconds))

    if on_progress:
        on_progress(100.0, "done")
    return {
        "windows": windows_out,
        "events": [],
        "elapsed_sec": time.monotonic() - t0,
    }


def run_real_live_session(
    contract: JobContract,
    *,
    window_seconds: float = 30.0,
    should_stop: Optional[StopFn] = None,
    on_progress: Optional[ProgressCb] = None,
    on_window: Optional[WindowCb] = None,
    on_heartbeat: Optional[HeartbeatCb] = None,
    on_preview: Optional[PreviewCb] = None,
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Real vision live loop — sample until stop (or file EOF)."""
    from worker import capture, config, debug_overlay, regions, vision_mediapipe
    from worker.aggregation import aggregate_windows

    cfg = config.load_config(config_path)
    wlen = float(window_seconds or 30.0)
    fps = float(config.sampling_fps(cfg) or 1.5)

    source: Any = contract.video_path or contract.source_url
    if not source:
        raise ValueError("No video_path or source_url for live session")

    def _hb(hint: str, **extra: Any) -> None:
        if not on_heartbeat:
            return
        payload: Dict[str, Any] = {
            "persons_detected": 0,
            "persons_in_seats": 0,
            "time_sec": 0.0,
            "detection_hint": hint,
            **extra,
        }
        on_heartbeat(payload)

    # Drawn room boxes are not seats. Faces register their own slots.
    facing_mode = (contract.facing_mode or "").strip().lower()
    phone_source = isinstance(source, str) and source.lower().startswith("browser:")
    if facing_mode == "toward_camera" or phone_source or not contract.target_roi:
        facing = (0.0, -1.0)
    else:
        target = regions.parse_target(contract.target_roi)
        if target is None:
            facing = (0.0, -1.0)
        else:
            facing = regions.teaching_target_geometry(target, []).facing_vector_norm

    # Faces register seats. Body boxes are not seats, so live does not load YOLO.
    _hb("Loading face model (first Start can take a few seconds)…")
    if on_progress:
        on_progress(4.0, "loading_models")
    tiers = cfg.get("tiers") or {}
    # Classroom webcam: faces are smaller — allow a face a bit earlier
    face_min = min(float(config.face_width_min_px(cfg)), 56.0)
    landmarker = None
    if bool(tiers.get("enable_tier2_head_pose", True)):
        _hb("Loading face landmarker…")
        try:
            mp_path = (cfg.get("models") or {}).get("mediapipe_face_landmarker")
            resolved_mp = config.resolve_model_path(
                mp_path if isinstance(mp_path, str) else None
            )
            landmarker = vision_mediapipe.load_face_landmarker(resolved_mp, num_faces=20)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Face landmarker unavailable in live: %s", exc)
            landmarker = None

    orientation = cfg.get("orientation") or {}
    pitch_down = float(orientation.get("pitch_down_threshold_deg", 20.0))
    yaw_thr = float(orientation.get("yaw_threshold_deg", 30.0))
    tier1_yaw = float(orientation.get("tier1_yaw_threshold_deg", 45.0))

    # Webcam: open only after models are warm (browser should already have released)
    if isinstance(source, str) and source.lower().startswith("webcam:"):
        try:
            preferred = int(source.split(":", 1)[1])
        except ValueError:
            preferred = 0
        _hb("Opening worker camera…")
        resolved, luma = capture.resolve_webcam_source(preferred)
        logger.info("Live webcam resolved %s → %s (luma=%.1f)", source, resolved, luma)
        source = resolved
        time.sleep(0.35)
        _hb(
            f"Camera {resolved} open (brightness {luma:.0f}) — detecting…",
            worker_source=resolved,
            frame_luma=luma,
        )

    buffer: List[Any] = []
    windows_out: List[Dict[str, Any]] = []
    window_index = 0
    frame_i = 0
    t_start = time.monotonic()
    preview_fps = 12.0
    metric_fps = max(float(fps), 2.5)
    metric_interval = 1.0 / metric_fps
    next_metric_at = 0.0
    registrar = FaceSeatRegistrar()
    last_boxes: List[Any] = []

    def _seat_rows(feats: Sequence[Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for feat in feats:
            usable = bool(feat.is_observable())
            orient = None
            if usable and feat.target_oriented is True:
                orient = 90.0
            elif usable and feat.target_oriented is False:
                orient = 30.0
            rows.append(
                {
                    "seat_id": feat.seat_id,
                    "orientation_pct": orient,
                    "usable": usable,
                }
            )
        return rows

    if on_progress:
        on_progress(8.0, "ingest")

    browser_cam = isinstance(source, str) and source.lower().startswith("browser:")
    if browser_cam:
        def _pull_phone_jpeg() -> tuple:
            from app.cache.redis_client import get_live_ingest_jpeg

            return get_live_ingest_jpeg(contract.session_id)

        _hb("Waiting for this phone's camera… allow the permission prompt.")
        frame_iter = capture.iter_pushed_jpegs(
            _pull_phone_jpeg,
            sample_fps=preview_fps,
            should_stop=should_stop,
            on_waiting=lambda msg: _hb(msg),
        )
    else:
        frame_iter = capture.iter_sampled_frames(
            source,
            sample_fps=preview_fps,
            max_frames=None,
            config_path=config_path,
        )

    for frame in frame_iter:
        if should_stop and should_stop():
            break

        if on_preview:
            try:
                jpeg = debug_overlay.encode_face_preview_jpeg(
                    frame.image,
                    last_boxes,
                    quality=82,
                    max_width=1100,
                    banner=registrar.hint(float(frame.time_sec)),
                )
                if jpeg:
                    on_preview(jpeg)
            except Exception as exc:  # noqa: BLE001
                if frame_i < 3:
                    logger.warning(
                        "live preview encode skipped: %s: %s",
                        type(exc).__name__,
                        exc,
                    )

        # Face landmarker stays on this thread. Seats come only from stable faces.
        if frame.time_sec + 1e-6 >= next_metric_at:
            next_metric_at = float(frame.time_sec) + metric_interval
            m_time = float(frame.time_sec)
            luma = capture.frame_mean_luma(frame.image)
            if landmarker is None:
                sightings = []
                hint = "Face model did not load — no seats will be registered."
            else:
                sightings = vision_mediapipe.face_sightings_from_frame(
                    landmarker,
                    frame.image,
                    time_sec=m_time,
                    min_eye_px=min(face_min, 18.0),
                )
                hint = registrar.hint(m_time)
            last_boxes = registrar.update(
                sightings,
                time_sec=m_time,
                frame_width=frame.width,
                frame_height=frame.height,
            )
            if luma < 8.0:
                hint = (
                    "Frames are almost black — check that the phone camera is allowed "
                    "and the lens is uncovered."
                )
            elif not last_boxes and luma >= 8.0 and landmarker is not None:
                hint = registrar.hint(m_time)
            feats = registrar.to_features(
                m_time,
                facing_vector_norm=facing,
                yaw_threshold_deg=yaw_thr,
                pitch_down_threshold_deg=pitch_down,
            )
            locked = registrar.locked_ids()
            if on_heartbeat:
                on_heartbeat(
                    {
                        "persons_detected": len(sightings),
                        "persons_in_seats": len(locked),
                        "time_sec": m_time,
                        "detection_hint": hint,
                        "frame_luma": luma,
                        "worker_source": source if isinstance(source, str) else None,
                        "preview_fps": preview_fps,
                        "metric_fps": metric_fps,
                        "tracked_seats": len(locked),
                        "per_seat": _seat_rows(feats),
                    }
                )
            buffer.extend(feats)
            while True:
                w_end = (window_index + 1) * wlen
                if m_time < w_end - 1e-6:
                    break
                w_start = window_index * wlen
                chunk = [f for f in buffer if w_start <= f.time_sec < w_end]
                buffer = [f for f in buffer if f.time_sec >= w_end]
                win_ids = list(registrar.locked_ids())
                if not win_ids:
                    window_index += 1
                    continue
                wins = aggregate_windows(
                    chunk,
                    expected_seat_ids=win_ids,
                    window_seconds=wlen,
                    topics=contract.topics,
                    modes=contract.modes,
                    sample_interval_sec=1.0 / metric_fps,
                    min_usable_seats=1,
                    min_coverage_pct=1.0,
                    min_usable_sample_frac=0.20,
                )
                if wins:
                    w = wins[0]
                    w["start_sec"] = float(w_start)
                    w["end_sec"] = float(w_end)
                    per_seat = _per_seat_from_features(
                        chunk,
                        win_ids,
                        teaching_mode=str(w.get("teaching_mode") or "explanation"),
                        yaw_threshold_deg=yaw_thr,
                        tier1_yaw_threshold_deg=tier1_yaw,
                    )
                    w["seat_stats"] = per_seat
                    groups = cluster_low_orientation_seats(per_seat)
                    windows_out.append(w)
                    if on_window:
                        on_window(w, per_seat, groups)
                window_index += 1
                if on_progress:
                    elapsed = time.monotonic() - t_start
                    on_progress(min(90.0, 10.0 + (elapsed % 80)), "vision")

        frame_i += 1
        if contract.video_path and frame.time_sec > float(contract.duration_sec or 1e12):
            break

    if buffer:
        w_start = window_index * wlen
        w_end = w_start + wlen
        win_ids = list(registrar.locked_ids())
        if not win_ids:
            wins = []
        else:
            wins = aggregate_windows(
                buffer,
                expected_seat_ids=win_ids,
                window_seconds=wlen,
                topics=contract.topics,
                modes=contract.modes,
                sample_interval_sec=1.0 / metric_fps,
                partial_window_min_seconds=5.0,
                min_usable_seats=1,
                min_coverage_pct=1.0,
                min_usable_sample_frac=0.20,
            )
        if wins:
            w = wins[0]
            w["start_sec"] = float(w_start)
            w["end_sec"] = float(
                min(w_end, max(f.time_sec for f in buffer) + 1e-3)
            )
            per_seat = _per_seat_from_features(
                buffer,
                win_ids,
                teaching_mode=str(w.get("teaching_mode") or "explanation"),
                yaw_threshold_deg=yaw_thr,
                tier1_yaw_threshold_deg=tier1_yaw,
            )
            w["seat_stats"] = per_seat
            groups = cluster_low_orientation_seats(per_seat)
            windows_out.append(w)
            if on_window:
                on_window(w, per_seat, groups)

    if on_progress:
        on_progress(95.0, "aggregate")

    return {
        "windows": windows_out,
        "events": [],
        "elapsed_sec": time.monotonic() - t_start,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }


def _per_seat_from_features(
    features: Sequence[Any],
    expected_ids: Sequence[str],
    *,
    teaching_mode: str,
    yaw_threshold_deg: float = 30.0,
    tier1_yaw_threshold_deg: float = 45.0,
) -> List[Dict[str, Any]]:
    from worker.features import sample_aligned

    by: Dict[str, List[Any]] = defaultdict(list)
    for f in features:
        by[f.seat_id].append(f)
    out: List[Dict[str, Any]] = []
    for sid in expected_ids:
        samples = by.get(sid, [])
        obs = [s for s in samples if s.is_observable()]
        if len(obs) < 1:
            out.append({"seat_id": sid, "orientation_pct": None, "usable": False})
            continue
        flags = []
        for s in obs:
            al = sample_aligned(
                s,
                teaching_mode=teaching_mode,
                yaw_threshold_deg=yaw_threshold_deg,
                tier1_yaw_threshold_deg=tier1_yaw_threshold_deg,
            )
            if al is not None:
                flags.append(al)
        if not flags:
            out.append({"seat_id": sid, "orientation_pct": None, "usable": False})
            continue
        o = 100.0 * sum(1 for a in flags if a) / len(flags)
        out.append({"seat_id": sid, "orientation_pct": round(o, 1), "usable": True})
    return out
