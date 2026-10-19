"""Phase 19 — window aggregation / coverage / TTOI fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from worker.aggregation import aggregate_windows
from worker.features import SeatFrameFeature


def _feat(
    seat: str,
    t: float,
    *,
    yaw: float = 10.0,
    head_down: bool = False,
    occupied: bool = True,
    tier: int | None = 1,
) -> SeatFrameFeature:
    return SeatFrameFeature(
        seat_id=seat,
        time_sec=t,
        occupied=occupied,
        target_oriented=abs(yaw) <= 30 and not head_down,
        yaw_prime_deg=yaw if occupied and tier else None,
        pitch_deg=25.0 if head_down else 5.0,
        head_down_cue=head_down,
        tier=tier if occupied else None,
        person_conf=0.9 if occupied else None,
        data_quality_note=None if occupied else "empty",
    )


def test_ttoi_high_when_all_oriented():
    seats = [f"s{i}" for i in range(6)]
    feats = []
    for t in range(0, 20):  # ≥15s usable span
        for s in seats:
            feats.append(_feat(s, float(t), yaw=5.0))
    windows = aggregate_windows(
        feats,
        expected_seat_ids=seats,
        window_seconds=30.0,
        min_usable_seats=5,
        sample_interval_sec=1.0,
    )
    assert len(windows) == 1
    w = windows[0]
    assert w["coverage_pct"] == 100.0
    assert w["usable_regions"] == 6
    assert w["ttoi"] is not None and w["ttoi"] >= 95.0
    assert w["data_quality_note"] is None


def test_insufficient_coverage_nulls_ttoi():
    seats = [f"s{i}" for i in range(10)]
    # Only 2 seats observable → coverage 20%
    feats = [_feat("s0", 0.0), _feat("s1", 0.0)]
    windows = aggregate_windows(
        feats,
        expected_seat_ids=seats,
        window_seconds=30.0,
        min_coverage_pct=70.0,
        min_usable_seats=5,
        sample_interval_sec=1.0,
    )
    w = windows[0]
    assert w["data_quality_note"] == "insufficient_coverage"
    assert w["ttoi"] is None


def test_note_taking_head_down_not_failure():
    seats = [f"s{i}" for i in range(6)]
    feats = []
    for t in [0.0, 1.0]:
        for s in seats:
            feats.append(_feat(s, t, yaw=10.0, head_down=True))
    windows = aggregate_windows(
        feats,
        expected_seat_ids=seats,
        window_seconds=30.0,
        modes=[{"mode": "note_taking", "start_sec": 0.0}],
        respect_teaching_modes=True,
        sample_interval_sec=1.0,
        head_down_min_seconds=1.0,
    )
    w = windows[0]
    assert w["ttoi"] is not None and w["ttoi"] >= 95.0
    assert w["head_down_cue_pct"] > 0


def test_explanation_head_down_lowers_ttoi():
    seats = [f"s{i}" for i in range(6)]
    feats = []
    for t in [0.0, 1.0]:
        for s in seats:
            feats.append(_feat(s, t, yaw=10.0, head_down=True))
    windows = aggregate_windows(
        feats,
        expected_seat_ids=seats,
        window_seconds=30.0,
        modes=[{"mode": "explanation", "start_sec": 0.0}],
        respect_teaching_modes=True,
        sample_interval_sec=1.0,
    )
    w = windows[0]
    assert w["ttoi"] is not None and w["ttoi"] <= 5.0


def test_partial_window_flag():
    seats = [f"s{i}" for i in range(6)]
    # Single sample → ~1s usable < 15s partial
    feats = [_feat(s, 0.0) for s in seats]
    windows = aggregate_windows(
        feats,
        expected_seat_ids=seats,
        window_seconds=30.0,
        partial_window_min_seconds=15.0,
        sample_interval_sec=1.0,
    )
    # Coverage OK but partial
    assert windows[0]["data_quality_note"] == "partial_window"
