"""Phase 21 — scripted threshold / honesty fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from worker.aggregation import aggregate_windows
from worker.config import (
    face_width_min_px,
    load_config,
    min_coverage_pct,
    min_usable_seats,
    pitch_down_threshold_deg,
    tier1_yaw_threshold_deg,
    yaw_threshold_deg,
)
from worker.features import SeatFrameFeature, sample_aligned


def _f(
    yaw: float,
    *,
    tier: int = 2,
    head_down: bool = False,
    t: float = 0.0,
    seat: str = "s0",
) -> SeatFrameFeature:
    return SeatFrameFeature(
        seat_id=seat,
        time_sec=t,
        occupied=True,
        yaw_prime_deg=yaw,
        pitch_deg=28.0 if head_down else 5.0,
        head_down_cue=head_down,
        tier=tier,
        person_conf=0.9,
    )


def test_config_pilot_defaults():
    cfg = load_config()
    assert yaw_threshold_deg(cfg) == 30.0
    assert tier1_yaw_threshold_deg(cfg) == 45.0
    assert pitch_down_threshold_deg(cfg) == 20.0
    assert face_width_min_px(cfg) == 80.0
    assert min_coverage_pct(cfg) == 70.0
    assert min_usable_seats(cfg) == 5


def test_face_board_vs_turn_away():
    assert sample_aligned(_f(10.0), yaw_threshold_deg=30) is True
    assert sample_aligned(_f(48.0), yaw_threshold_deg=30) is False


def test_head_down_mode_hook():
    hd = _f(10.0, head_down=True)
    assert sample_aligned(hd, teaching_mode="explanation") is False
    assert sample_aligned(hd, teaching_mode="note_taking") is True


def test_tier1_wider_yaw_band():
    # 35° fails Tier-2 band, passes Tier-1 band
    f = _f(35.0, tier=1)
    assert (
        sample_aligned(f, yaw_threshold_deg=30.0, tier1_yaw_threshold_deg=45.0)
        is True
    )
    f2 = _f(35.0, tier=2)
    assert (
        sample_aligned(f2, yaw_threshold_deg=30.0, tier1_yaw_threshold_deg=45.0)
        is False
    )


def test_low_coverage_nulls_ttoi_no_invented_score():
    seats = [f"s{i}" for i in range(8)]
    feats = [_f(5.0, t=float(t), seat="s0") for t in range(20)]
    feats += [_f(5.0, t=float(t), seat="s1") for t in range(20)]
    windows = aggregate_windows(
        feats,
        expected_seat_ids=seats,
        window_seconds=30.0,
        partial_window_min_seconds=1.0,
        min_coverage_pct=70.0,
        min_usable_seats=5,
        sample_interval_sec=1.0,
    )
    assert windows[0]["ttoi"] is None
    assert windows[0]["data_quality_note"] == "insufficient_coverage"
