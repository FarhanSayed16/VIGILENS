"""Phase 19 — decline smoothing / baseline / persist fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from worker.drop_events import detect_declines


def _win(
    i: int,
    ttoi: float,
    *,
    coverage: float = 85.0,
    usable: int = 10,
    quality: str | None = None,
    wlen: float = 30.0,
) -> dict:
    return {
        "start_sec": i * wlen,
        "end_sec": (i + 1) * wlen,
        "topic_id": 1,
        "teaching_mode": "explanation",
        "expected_regions": 12,
        "usable_regions": usable,
        "coverage_pct": coverage,
        "ttoi": ttoi,
        "ttoi_lo": ttoi - 3,
        "ttoi_hi": ttoi + 3,
        "head_down_cue_pct": 10.0,
        "hand_raise_events": 0,
        "candidate_decline": False,
        "dominant_cue": "target_oriented",
        "data_quality_note": quality,
    }


def test_decline_flagged_after_persist():
    # 6 calm windows @ 80, then drop to 60 for 3 windows
    windows = [_win(i, 80.0) for i in range(6)] + [_win(6 + i, 60.0) for i in range(3)]
    events = detect_declines(
        windows,
        window_seconds=30.0,
        smooth_median_seconds=90.0,
        baseline_seconds=180.0,
        min_drop_points=10.0,
        min_persist_windows=2,
    )
    assert any(w["candidate_decline"] for w in windows)
    assert len(events) >= 1
    assert events[0]["depth"] >= 10.0
    assert events[0]["end_sec"] > events[0]["start_sec"]


def test_no_decline_when_low_coverage():
    windows = [_win(i, 80.0) for i in range(6)] + [
        _win(6 + i, 50.0, coverage=40.0, usable=3, quality="insufficient_coverage")
        for i in range(3)
    ]
    events = detect_declines(windows, min_drop_points=10.0, min_persist_windows=2)
    assert events == []
    assert not any(w["candidate_decline"] for w in windows)


def test_no_decline_on_partial_windows():
    windows = [_win(i, 80.0) for i in range(6)] + [
        _win(6 + i, 50.0, quality="partial_window") for i in range(3)
    ]
    events = detect_declines(windows)
    assert events == []


def test_single_window_drop_does_not_persist():
    windows = [_win(i, 80.0) for i in range(6)] + [_win(6, 55.0)]
    events = detect_declines(windows, min_persist_windows=2)
    assert events == []
    assert not any(w["candidate_decline"] for w in windows)
