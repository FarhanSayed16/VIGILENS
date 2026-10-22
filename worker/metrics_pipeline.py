"""
Offline TTOI pipeline: features → windows → decline events (Phase 19).

Does not require backend or GPU when fed seat features (fixtures / CLI).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from worker import aggregation, config, drop_events
from worker.features import SeatFrameFeature


def build_results_from_features(
    features: Sequence[SeatFrameFeature],
    *,
    expected_seat_ids: Sequence[str],
    cfg: Optional[Dict[str, Any]] = None,
    topics: Optional[Sequence[Dict[str, Any]]] = None,
    modes: Optional[Sequence[Dict[str, Any]]] = None,
    sample_interval_sec: Optional[float] = None,
) -> Dict[str, Any]:
    """Aggregate + detect declines → WorkerResultPayload-shaped dict."""
    cfg = cfg if cfg is not None else config.load_config()
    sampling = cfg.get("sampling") or {}
    coverage = cfg.get("coverage") or {}
    orientation = cfg.get("orientation") or {}
    decline = cfg.get("decline") or {}
    modes_cfg = cfg.get("modes") or {}

    window_seconds = float(sampling.get("window_seconds", 30.0))
    windows = aggregation.aggregate_windows(
        features,
        expected_seat_ids=expected_seat_ids,
        window_seconds=window_seconds,
        partial_window_min_seconds=float(
            sampling.get("partial_window_min_seconds", 15.0)
        ),
        min_usable_sample_frac=float(sampling.get("min_usable_sample_frac", 0.5)),
        min_coverage_pct=float(coverage.get("min_coverage_pct", 70.0)),
        min_usable_seats=int(coverage.get("min_usable_seats", 5)),
        yaw_threshold_deg=float(orientation.get("yaw_threshold_deg", 30.0)),
        tier1_yaw_threshold_deg=float(
            orientation.get("tier1_yaw_threshold_deg", 45.0)
        ),
        head_down_min_seconds=float(orientation.get("head_down_min_seconds", 8.0)),
        respect_teaching_modes=bool(modes_cfg.get("respect_teaching_modes", True)),
        topics=topics,
        modes=modes,
        sample_interval_sec=sample_interval_sec
        or (1.0 / max(config.sampling_fps(cfg), 0.1)),
    )
    events = drop_events.detect_declines(
        windows,
        window_seconds=window_seconds,
        smooth_median_seconds=float(decline.get("smooth_median_seconds", 90.0)),
        baseline_seconds=float(decline.get("baseline_seconds", 180.0)),
        min_drop_points=float(decline.get("min_drop_points", 10.0)),
        min_persist_windows=int(decline.get("min_persist_windows", 2)),
        min_coverage_pct=float(coverage.get("min_coverage_pct", 70.0)),
        min_usable_seats=int(coverage.get("min_usable_seats", 5)),
    )
    return {"windows": windows, "events": events}


def make_fixture_features(
    *,
    seat_ids: Sequence[str],
    duration_sec: float = 600.0,
    sample_fps: float = 1.0,
    window_seconds: float = 30.0,
    dip_start_sec: float = 300.0,
    dip_end_sec: float = 420.0,
    oriented_frac_high: float = 0.85,
    oriented_frac_low: float = 0.45,
) -> List[SeatFrameFeature]:
    """
    Scripted classroom timeline for offline CLI / unit tests.

    High orientation, then a mid-lecture dip (candidate decline region).
    """
    seats = list(seat_ids)
    if not seats:
        raise ValueError("seat_ids required")
    dt = 1.0 / max(sample_fps, 0.1)
    features: List[SeatFrameFeature] = []
    t = 0.0
    idx = 0
    while t < duration_sec - 1e-9:
        in_dip = dip_start_sec <= t <= dip_end_sec
        frac = oriented_frac_low if in_dip else oriented_frac_high
        for si, sid in enumerate(seats):
            # Deterministic pseudo-random per seat/time
            h = (idx * 31 + si * 17) % 100
            oriented = (h / 100.0) < frac
            yaw = 8.0 if oriented else 48.0
            # Sign alternates
            if si % 2:
                yaw = -yaw
            features.append(
                SeatFrameFeature(
                    seat_id=sid,
                    time_sec=t,
                    occupied=True,
                    target_oriented=oriented,
                    yaw_prime_deg=yaw,
                    pitch_deg=5.0 if oriented else 12.0,
                    head_down_cue=False,
                    hand_raised=(si == 0 and idx % 40 == 0),
                    tier=1,
                    person_conf=0.9,
                )
            )
        t += dt
        idx += 1
    return features
