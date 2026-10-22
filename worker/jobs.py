"""
Worker job entrypoints.

- Fake path: worker.fake_worker (CI / USE_FAKE_WORKER=true)
- Real path: ingest + YOLO + MediaPipe + TTOI (Phase 20 default)
- Offline metrics: fixture features without vision (Phase 19)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from worker import capture, config, regions
from worker.fake_worker import JobContract, generate_synthetic_results

logger = logging.getLogger(__name__)

ProgressCb = Callable[[float, str], None]


def run_fake_job(contract: JobContract, **kwargs: Any) -> Dict[str, Any]:
    """Delegate to Phase 11 fake worker (stable API contract)."""
    return generate_synthetic_results(contract, **kwargs)


def run_real_job(
    contract: JobContract,
    *,
    on_progress: Optional[ProgressCb] = None,
    config_path: Optional[str] = None,
    max_frames: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Real CV pipeline (Phase 20): sample frames → YOLO → optional MediaPipe
    → seat features → TTOI windows → candidate declines.
    """
    from worker import (
        metrics_pipeline,
        seat_mapping,
        vision_mediapipe,
        vision_yolo,
    )
    from worker.features import features_from_frame_map

    def progress(pct: float, stage: str) -> None:
        if on_progress:
            on_progress(float(pct), stage)

    cfg = config.load_config(config_path)
    progress(5.0, "ingest")

    source: Any
    if contract.video_path:
        source = contract.video_path
    elif contract.source_url:
        source = contract.source_url
    else:
        raise ValueError("JobContract needs video_path or source_url for real job")

    info = capture.probe_source(source, config_path=config_path)
    logger.info(
        "Real job ingest session=%s source=%s %sx%s fps=%s frames=%s",
        contract.session_id,
        info.source_kind,
        info.width,
        info.height,
        info.fps_native,
        info.frame_count,
    )

    seats = regions.parse_seat_regions(contract.seat_regions)
    if not seats:
        raise ValueError(
            "Room has no seat_regions — calibrate seats in the Rooms UI before real analysis"
        )

    facing_mode = (contract.facing_mode or "").strip().lower()
    if facing_mode == "toward_camera":
        # Students face the lens (board behind camera). Looking at camera ⇒ oriented.
        facing = (0.0, -1.0)
    else:
        if not contract.target_roi:
            raise ValueError(
                "Room has no teaching target ROI — set the board/screen in Rooms, "
                "or use “Facing the students” (toward-camera) placement"
            )
        target = regions.parse_target(contract.target_roi)
        if target is None:
            raise ValueError(
                "Room teaching target ROI could not be parsed — re-draw the target in Rooms"
            )
        facing = regions.teaching_target_geometry(target, seats).facing_vector_norm

    progress(12.0, "ingest")

    weights_raw = (cfg.get("models") or {}).get("yolo_pose_weights", "yolov8n-pose.pt")
    weights_path = config.resolve_model_path(weights_raw)
    if not weights_path.is_file():
        # Keep auto-download under models/ (not process CWD / backend/)
        weights_path = config.REPO_ROOT / "models" / Path(str(weights_raw)).name
        weights_path.parent.mkdir(parents=True, exist_ok=True)
    weights = str(weights_path)
    model = vision_yolo.load_yolo_pose(weights)

    tiers = cfg.get("tiers") or {}
    enable_tier2 = bool(tiers.get("enable_tier2_head_pose", True))
    face_min = config.face_width_min_px(cfg)
    landmarker = None
    if enable_tier2:
        try:
            mp_path = (cfg.get("models") or {}).get("mediapipe_face_landmarker")
            resolved_mp = config.resolve_model_path(
                mp_path if isinstance(mp_path, str) else None
            )
            landmarker = vision_mediapipe.load_face_landmarker(resolved_mp)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Tier-2 MediaPipe unavailable, Tier-1 only: %s", exc)
            landmarker = None
            enable_tier2 = False

    progress(18.0, "vision")

    sample_fps = config.sampling_fps(cfg)
    samples = list(
        capture.iter_sampled_frames(
            source,
            sample_fps=sample_fps,
            max_frames=max_frames,
            config_path=config_path,
        )
    )
    if not samples:
        raise RuntimeError(f"No frames sampled from source: {source}")

    orientation = cfg.get("orientation") or {}
    pitch_down = float(orientation.get("pitch_down_threshold_deg", 20.0))
    yaw_thr = float(orientation.get("yaw_threshold_deg", 30.0))
    tier1_yaw = float(orientation.get("tier1_yaw_threshold_deg", 45.0))

    features: List[Any] = []
    frame_maps = []
    n = len(samples)
    for i, s in enumerate(samples):
        people = vision_yolo.detect_persons(model, s.image, conf=0.25)
        fmap = seat_mapping.assign_persons_to_seats(
            people,
            seats,
            frame_width=s.width,
            frame_height=s.height,
            time_sec=s.time_sec,
        )
        frame_maps.append(fmap)
        feats = features_from_frame_map(
            fmap,
            frame_bgr=s.image,
            landmarker=landmarker,
            face_width_min_px=face_min,
            pitch_down_threshold_deg=pitch_down,
            enable_tier2=enable_tier2 and landmarker is not None,
            facing_vector_norm=facing,
            yaw_threshold_deg=yaw_thr,
            tier1_yaw_threshold_deg=tier1_yaw,
        )
        features.extend(feats)
        pct = 18.0 + 62.0 * ((i + 1) / n)
        progress(pct, "vision")

    progress(82.0, "calibrate")
    occ_frac = float(
        (cfg.get("calibration") or {}).get("occupied_seat_min_fraction", 0.5)
    )
    # Prefer early window (~3 min) for N_expected — not the whole lecture dip
    calib_horizon = float(
        (cfg.get("calibration") or {}).get("horizon_seconds", 180.0)
    )
    calib_maps = [fm for fm in frame_maps if fm.time_sec <= calib_horizon] or list(
        frame_maps
    )
    calib = seat_mapping.calibrate_occupancy(
        calib_maps, seats, occupied_seat_min_fraction=occ_frac
    )
    # Prefer calibrated occupied seats; fall back to all configured seats
    expected_ids = list(calib.occupied_seat_ids) or [s.id for s in seats]
    logger.info(
        "Calibration N_expected=%s occupied=%s samples=%s features=%s",
        calib.n_expected,
        expected_ids,
        n,
        len(features),
    )

    progress(88.0, "aggregate")
    result = metrics_pipeline.build_results_from_features(
        features,
        expected_seat_ids=expected_ids,
        cfg=cfg,
        topics=contract.topics,
        modes=contract.modes,
        sample_interval_sec=1.0 / max(sample_fps, 0.1),
    )
    progress(96.0, "aggregate")
    return result


def run_offline_metrics(
    contract: JobContract,
    *,
    config_path: Optional[str] = None,
    features: Optional[List[Any]] = None,
    expected_seat_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Phase 19 offline path: seat features → windows + decline events.

    If features omitted, builds a scripted fixture timeline sized to contract.
    """
    from worker import metrics_pipeline

    cfg = config.load_config(config_path)
    seats = regions.parse_seat_regions(contract.seat_regions)
    seat_ids = expected_seat_ids or (
        [s.id for s in seats]
        if seats
        else [f"s{i+1}" for i in range(max(1, contract.seat_count))]
    )
    if features is None:
        features = metrics_pipeline.make_fixture_features(
            seat_ids=seat_ids,
            duration_sec=float(contract.duration_sec),
            sample_fps=config.sampling_fps(cfg),
            window_seconds=float(contract.window_seconds),
        )
    return metrics_pipeline.build_results_from_features(
        features,
        expected_seat_ids=seat_ids,
        cfg=cfg,
        topics=contract.topics,
        modes=contract.modes,
    )


def prepare_ingest(
    contract: JobContract,
    *,
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load config, probe source, parse seat/target geometry (no models).
    """
    cfg = config.load_config(config_path)
    source: Any
    if contract.video_path:
        source = contract.video_path
    elif contract.source_url:
        source = contract.source_url
    else:
        raise ValueError("JobContract needs video_path or source_url for ingest")

    info = capture.probe_source(source, config_path=config_path)
    seats = regions.parse_seat_regions(contract.seat_regions)
    target_raw = contract.target_roi
    target = regions.parse_target(target_raw) if target_raw else None
    geom = (
        regions.teaching_target_geometry(target, seats)
        if target is not None
        else None
    )

    return {
        "config_version": cfg.get("version"),
        "sample_fps": config.sampling_fps(cfg),
        "capture": {
            "source": info.source,
            "kind": info.source_kind,
            "fps_native": info.fps_native,
            "frame_count": info.frame_count,
            "width": info.width,
            "height": info.height,
        },
        "seats": len(seats),
        "target_centroid": geom.centroid_norm if geom else None,
        "facing_vector": geom.facing_vector_norm if geom else None,
        "weights": (cfg.get("models") or {}).get("yolo_pose_weights"),
    }


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
