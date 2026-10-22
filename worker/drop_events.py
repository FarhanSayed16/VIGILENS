"""
Candidate orientation decline detection (Phase 19).

Never label as boredom / attention failure in product copy.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence


def _rolling_median(values: Sequence[Optional[float]], k: int) -> List[Optional[float]]:
    """Causal rolling median over last k non-None-friendly window (uses available)."""
    out: List[Optional[float]] = []
    for i in range(len(values)):
        chunk = [v for v in values[max(0, i - k + 1) : i + 1] if v is not None]
        if not chunk:
            out.append(None)
            continue
        s = sorted(chunk)
        mid = len(s) // 2
        if len(s) % 2:
            out.append(s[mid])
        else:
            out.append(0.5 * (s[mid - 1] + s[mid]))
    return out


def _evidence_ok(window: Dict[str, Any], *, min_coverage_pct: float, min_usable_seats: int) -> bool:
    if window.get("data_quality_note") in ("insufficient_coverage", "partial_window"):
        return False
    cov = window.get("coverage_pct")
    usable = window.get("usable_regions")
    if cov is None or usable is None:
        return False
    if float(cov) < min_coverage_pct:
        return False
    if int(usable) < min_usable_seats:
        return False
    if window.get("ttoi") is None:
        return False
    return True


def detect_declines(
    windows: Sequence[Dict[str, Any]],
    *,
    window_seconds: float = 30.0,
    smooth_median_seconds: float = 90.0,
    baseline_seconds: float = 180.0,
    min_drop_points: float = 10.0,
    min_persist_windows: int = 2,
    min_coverage_pct: float = 70.0,
    min_usable_seats: int = 5,
) -> List[Dict[str, Any]]:
    """
    Method A: median-smooth TTOI, baseline = median of prior ~3 min, flag drops.

    Mutates windows in-place: sets candidate_decline True on flagged windows.
    Returns event dicts with depth = max drop over the flagged span.
    """
    if not windows:
        return []

    wlen = max(1e-6, float(window_seconds))
    smooth_k = max(1, int(round(smooth_median_seconds / wlen)))
    baseline_k = max(1, int(round(baseline_seconds / wlen)))

    ttoi_series: List[Optional[float]] = [
        float(w["ttoi"]) if w.get("ttoi") is not None else None for w in windows
    ]
    smooth = _rolling_median(ttoi_series, smooth_k)

    drops: List[Optional[float]] = []
    flags: List[bool] = []
    for i, w in enumerate(windows):
        if not _evidence_ok(
            w, min_coverage_pct=min_coverage_pct, min_usable_seats=min_usable_seats
        ):
            drops.append(None)
            flags.append(False)
            continue
        sm = smooth[i]
        if sm is None:
            drops.append(None)
            flags.append(False)
            continue
        # Baseline from previous smoothed windows only
        prior = [v for v in smooth[max(0, i - baseline_k) : i] if v is not None]
        if len(prior) < max(2, baseline_k // 2):
            drops.append(None)
            flags.append(False)
            continue
        prior_sorted = sorted(prior)
        mid = len(prior_sorted) // 2
        if len(prior_sorted) % 2:
            baseline = prior_sorted[mid]
        else:
            baseline = 0.5 * (prior_sorted[mid - 1] + prior_sorted[mid])
        drop = float(baseline) - float(sm)
        drops.append(drop)
        flags.append(drop >= min_drop_points)

    # Persist ≥ min_persist_windows consecutive flags
    candidate = [False] * len(windows)
    run = 0
    for i, f in enumerate(flags):
        if f:
            run += 1
        else:
            run = 0
        if run >= min_persist_windows:
            for j in range(i - min_persist_windows + 1, i + 1):
                candidate[j] = True

    for i, w in enumerate(windows):
        w["candidate_decline"] = bool(candidate[i])
        if candidate[i] and w.get("dominant_cue") in (None, "target_oriented"):
            w["dominant_cue"] = "yaw_away"

    # Merge consecutive candidate windows into events
    events: List[Dict[str, Any]] = []
    i = 0
    n = len(windows)
    while i < n:
        if not candidate[i]:
            i += 1
            continue
        j = i
        max_drop = drops[i] if drops[i] is not None else 0.0
        while j + 1 < n and candidate[j + 1]:
            j += 1
            if drops[j] is not None:
                max_drop = max(max_drop, float(drops[j]))
        w0, w1 = windows[i], windows[j]
        events.append(
            {
                "start_sec": float(w0["start_sec"]),
                "end_sec": float(w1["end_sec"]),
                "depth": round(float(max_drop), 1),
                "coverage_pct": w1.get("coverage_pct"),
                "topic_id": w1.get("topic_id"),
                "teaching_mode": w1.get("teaching_mode"),
                "dominant_cue": w1.get("dominant_cue") or "yaw_away",
                "note": (
                    "Candidate orientation decline "
                    "(observable TTOI drop vs recent baseline)."
                ),
            }
        )
        i = j + 1

    return events


def annotate_declines(
    windows: List[Dict[str, Any]],
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Alias that returns events after mutating windows."""
    return detect_declines(windows, **kwargs)
