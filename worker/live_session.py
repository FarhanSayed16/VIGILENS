"""
Streaming live lecture runner (Phase 27).

Captures until should_stop(), commits class + per-seat stats every window_seconds.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

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
    from worker import capture, config, debug_overlay, regions, seat_mapping, vision_mediapipe, vision_yolo
    from worker.aggregation import aggregate_windows
    from worker.features import features_from_frame_map

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

    seats = regions.parse_seat_regions(contract.seat_regions)
    if not seats:
        raise ValueError("Room has no seat regions — calibrate seats first")
    expected_ids = [s.id for s in seats]

    facing_mode = (contract.facing_mode or "").strip().lower()
    if facing_mode == "toward_camera":
        facing = (0.0, -1.0)
    else:
        if not contract.target_roi:
            raise ValueError("Room has no teaching target ROI")
        target = regions.parse_target(contract.target_roi)
        if target is None:
            raise ValueError("Teaching target ROI could not be parsed")
        facing = regions.teaching_target_geometry(target, seats).facing_vector_norm

    # Load vision BEFORE opening the webcam so the UI is not stuck on
    # "camera ready / 0 detected" for the multi-second first YOLO load.
    _hb("Loading vision model (first Start can take ~10s)…")
    if on_progress:
        on_progress(4.0, "loading_models")
    weights_raw = (cfg.get("models") or {}).get(
        "yolo_pose_weights", "models/yolov8n-pose.pt"
    )
    weights_path = config.resolve_model_path(weights_raw)
    if not weights_path.is_file():
        weights_path = config.REPO_ROOT / "models" / Path(str(weights_raw)).name
    model = vision_yolo.load_yolo_pose(str(weights_path))
    logger.info("Live YOLO ready: %s", weights_path)

    tiers = cfg.get("tiers") or {}
    enable_tier2 = bool(tiers.get("enable_tier2_head_pose", True))
    # Classroom webcam: faces are smaller — allow Tier-2 a bit earlier
    face_min = min(float(config.face_width_min_px(cfg)), 56.0)
    landmarker = None
    if enable_tier2:
        _hb("Loading face landmarker…")
        try:
            mp_path = (cfg.get("models") or {}).get("mediapipe_face_landmarker")
            resolved_mp = config.resolve_model_path(
                mp_path if isinstance(mp_path, str) else None
            )
            landmarker = vision_mediapipe.load_face_landmarker(resolved_mp)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Tier-2 unavailable in live: %s", exc)
            landmarker = None
            enable_tier2 = False

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
    # Preview on main thread; YOLO async so detection never freezes the feed
    preview_fps = 18.0
    metric_fps = max(float(fps), 2.5)
    metric_interval = 1.0 / metric_fps
    next_metric_at = 0.0
    last_fmap = seat_mapping.FrameSeatMap(
        time_sec=0.0,
        persons=[],
        seat_to_person_indices={s.id: [] for s in seats},
        unassigned_indices=[],
    )
    # Rolling set of seat ids (room + virtual) seen recently — class size can change
    active_seat_ids: List[str] = list(expected_ids)
    fmap_lock = threading.Lock()
    metric_busy = threading.Event()
    result_q: Queue[
        Tuple[float, Any, Any, float, int, int]
    ] = Queue(maxsize=2)

    def _merge_active_seats(fmap: Any) -> List[str]:
        nonlocal active_seat_ids
        seen = list(active_seat_ids)
        for sid, idxs in (fmap.seat_to_person_indices or {}).items():
            if idxs and sid not in seen:
                seen.append(str(sid))
        # Drop stale virtual seats not present this frame (people left)
        present = {
            str(sid)
            for sid, idxs in (fmap.seat_to_person_indices or {}).items()
            if idxs
        }
        room = set(expected_ids)
        kept = [s for s in seen if s in room or s in present]
        for sid in present:
            if sid not in kept:
                kept.append(sid)
        active_seat_ids = kept
        return active_seat_ids

    def _detect_async(
        image: Any, time_sec: float, width: int, height: int
    ) -> None:
        nonlocal last_fmap
        try:
            luma = capture.frame_mean_luma(image)
            det_image = capture.enhance_for_detection(image)
            # Full imgsz + high max_det for multi-student classroom frames
            people = vision_yolo.detect_persons(
                model,
                det_image,
                conf=0.12,
                imgsz=640,
                max_det=80,
                iou=0.50,
            )
            if not people and luma >= 8.0:
                people = vision_yolo.detect_persons(
                    model,
                    det_image,
                    conf=0.05,
                    imgsz=640,
                    max_det=80,
                    iou=0.50,
                )
            fmap = seat_mapping.assign_persons_to_seats(
                people,
                seats,
                frame_width=width,
                frame_height=height,
                time_sec=time_sec,
                soft_radius_norm=0.18,
                virtual_for_unassigned=True,
                max_virtual_seats=60,
            )
            in_seats = sum(1 for v in fmap.seat_to_person_indices.values() if v)
            with fmap_lock:
                last_fmap = fmap
            try:
                result_q.put_nowait(
                    (time_sec, det_image, fmap, luma, len(people), in_seats)
                )
            except Exception:  # noqa: BLE001
                pass
        except Exception as exc:  # noqa: BLE001
            logger.warning("async detect failed: %s", type(exc).__name__)
        finally:
            metric_busy.clear()

    if on_progress:
        on_progress(8.0, "ingest")

    for frame in capture.iter_sampled_frames(
        source,
        sample_fps=preview_fps,
        max_frames=None,
        config_path=config_path,
    ):
        if should_stop and should_stop():
            break

        with fmap_lock:
            overlay_map = last_fmap

        # Fast path: clear preview every grabbed frame (boxes from last detect)
        if on_preview:
            try:
                jpeg = debug_overlay.encode_live_preview_jpeg(
                    frame.image,
                    seats,
                    overlay_map,
                    quality=82,
                    max_width=1100,
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

        # Apply finished detections on the main thread (MediaPipe is not threaded)
        while True:
            try:
                (
                    m_time,
                    det_image,
                    fmap,
                    luma,
                    n_people,
                    in_seats,
                ) = result_q.get_nowait()
            except Empty:
                break
            with fmap_lock:
                last_fmap = fmap
            track_ids = _merge_active_seats(fmap)
            if on_heartbeat:
                if luma < 8.0:
                    hint = (
                        "Worker frames are almost black — another app may still own "
                        "the camera. Stop browser preview apps and Restart lecture."
                    )
                elif n_people == 0:
                    hint = (
                        f"No people in view (brightness {luma:.0f}). "
                        "Face the lens; classmates can sit anywhere in frame."
                    )
                else:
                    hint = (
                        f"Detecting {n_people} people — {in_seats} tracked "
                        f"(room seats + auto slots; class can grow/shrink live)"
                    )
                on_heartbeat(
                    {
                        "persons_detected": n_people,
                        "persons_in_seats": in_seats,
                        "time_sec": float(m_time),
                        "detection_hint": hint,
                        "frame_luma": luma,
                        "worker_source": source if isinstance(source, str) else None,
                        "preview_fps": preview_fps,
                        "metric_fps": metric_fps,
                        "tracked_seats": len(track_ids),
                    }
                )
            feats = features_from_frame_map(
                fmap,
                frame_bgr=det_image,
                landmarker=landmarker,
                face_width_min_px=face_min,
                pitch_down_threshold_deg=pitch_down,
                enable_tier2=enable_tier2 and landmarker is not None,
                facing_vector_norm=facing,
                yaw_threshold_deg=yaw_thr,
                tier1_yaw_threshold_deg=tier1_yaw,
            )
            buffer.extend(feats)
            while True:
                w_end = (window_index + 1) * wlen
                if m_time < w_end - 1e-6:
                    break
                w_start = window_index * wlen
                chunk = [f for f in buffer if w_start <= f.time_sec < w_end]
                buffer = [f for f in buffer if f.time_sec >= w_end]
                # Expected = room seats + any virtual ids present in this window
                win_ids = list(expected_ids)
                for f in chunk:
                    if f.seat_id and f.seat_id not in win_ids:
                        win_ids.append(f.seat_id)
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

        if frame.time_sec + 1e-6 >= next_metric_at and not metric_busy.is_set():
            next_metric_at = float(frame.time_sec) + metric_interval
            metric_busy.set()
            img_copy = frame.image.copy()
            threading.Thread(
                target=_detect_async,
                args=(img_copy, float(frame.time_sec), frame.width, frame.height),
                name="vigilens-detect",
                daemon=True,
            ).start()

        frame_i += 1
        if contract.video_path and frame.time_sec > float(contract.duration_sec or 1e12):
            break

    # Drain any in-flight detect before finalize
    if metric_busy.is_set():
        metric_busy.wait(timeout=5.0)
    while True:
        try:
            m_time, det_image, fmap, luma, n_people, in_seats = result_q.get_nowait()
        except Empty:
            break
        with fmap_lock:
            last_fmap = fmap
        feats = features_from_frame_map(
            fmap,
            frame_bgr=det_image,
            landmarker=landmarker,
            face_width_min_px=face_min,
            pitch_down_threshold_deg=pitch_down,
            enable_tier2=enable_tier2 and landmarker is not None,
            facing_vector_norm=facing,
            yaw_threshold_deg=yaw_thr,
            tier1_yaw_threshold_deg=tier1_yaw,
        )
        buffer.extend(feats)

    if buffer:
        w_start = window_index * wlen
        w_end = w_start + wlen
        win_ids = list(expected_ids)
        for f in buffer:
            if f.seat_id and f.seat_id not in win_ids:
                win_ids.append(f.seat_id)
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
