"""
Window aggregation → class-level TTOI / coverage (Phase 19).

Output dicts match backend WorkerResultPayload window fields.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from worker.features import SeatFrameFeature, sample_aligned

ModeLookup = Callable[[float], Optional[str]]
TopicLookup = Callable[[float], Optional[int]]


def _active_mode(modes: Sequence[Dict[str, Any]], t: float) -> Optional[str]:
    chosen = None
    for m in modes:
        if float(m.get("start_sec") or 0) <= t:
            if chosen is None or float(m["start_sec"]) >= float(chosen["start_sec"]):
                chosen = m
    return str(chosen["mode"]) if chosen else None


def _active_topic_id(topics: Sequence[Dict[str, Any]], t: float) -> Optional[int]:
    active = None
    for topic in topics:
        start = float(topic.get("start_sec") or 0)
        end = topic.get("end_sec")
        if start <= t and (end is None or float(end) >= t):
            if active is None or start >= float(active.get("start_sec") or 0):
                active = topic
    return int(active["id"]) if active and active.get("id") is not None else None


def _bootstrap_ci(
    values: Sequence[float],
    *,
    iters: int = 200,
    seed: int = 0,
) -> Tuple[float, float]:
    """Percentile bootstrap CI for the mean; falls back to ±0 if empty."""
    if not values:
        return 0.0, 0.0
    import random

    rng = random.Random(seed)
    n = len(values)
    means: List[float] = []
    for _ in range(max(20, iters)):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(0.025 * (len(means) - 1))]
    hi = means[int(0.975 * (len(means) - 1))]
    return lo, hi


def aggregate_windows(
    features: Sequence[SeatFrameFeature],
    *,
    expected_seat_ids: Sequence[str],
    window_seconds: float = 30.0,
    partial_window_min_seconds: float = 15.0,
    min_usable_sample_frac: float = 0.5,
    min_coverage_pct: float = 70.0,
    min_usable_seats: int = 5,
    yaw_threshold_deg: float = 30.0,
    tier1_yaw_threshold_deg: float = 45.0,
    head_down_min_seconds: float = 8.0,
    respect_teaching_modes: bool = True,
    topics: Optional[Sequence[Dict[str, Any]]] = None,
    modes: Optional[Sequence[Dict[str, Any]]] = None,
    sample_interval_sec: Optional[float] = None,
    bootstrap_iters: int = 200,
) -> List[Dict[str, Any]]:
    """
    Bucket per-seat frame features into fixed windows and compute TTOI / coverage.

    TTOI = 100 × mean(O_i) over usable seats; None when coverage gate fails.
    """
    if not expected_seat_ids:
        return []
    topics = list(topics or [])
    modes = list(modes or [])
    wlen = float(window_seconds)
    if wlen <= 0:
        raise ValueError("window_seconds must be positive")

    if not features:
        return []

    t_max = max(f.time_sec for f in features)
    n_windows = max(1, int(math.ceil((t_max + 1e-9) / wlen)))

    # Infer sample spacing for duration estimates
    times = sorted({round(f.time_sec, 6) for f in features})
    if sample_interval_sec is None:
        if len(times) >= 2:
            deltas = [times[i + 1] - times[i] for i in range(len(times) - 1)]
            sample_interval_sec = max(0.1, sum(deltas) / len(deltas))
        else:
            sample_interval_sec = 1.0

    # Index: window_i → seat_id → list[SeatFrameFeature]
    buckets: Dict[int, Dict[str, List[SeatFrameFeature]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for feat in features:
        wi = int(feat.time_sec // wlen)
        if wi < 0:
            wi = 0
        if wi >= n_windows:
            wi = n_windows - 1
        buckets[wi][feat.seat_id].append(feat)

    expected_n = len(expected_seat_ids)
    windows: List[Dict[str, Any]] = []

    for i in range(n_windows):
        start = i * wlen
        end = start + wlen
        mid = (start + end) / 2.0
        mode = _active_mode(modes, mid) or "explanation"
        topic_id = _active_topic_id(topics, mid)
        seat_bucket = buckets.get(i, {})

        o_rates: List[float] = []
        usable_ids: List[str] = []
        head_down_sustained = 0
        hand_raise_events = 0
        dominant_counts: Dict[str, int] = defaultdict(int)
        usable_span_sec = 0.0

        for sid in expected_seat_ids:
            samples = seat_bucket.get(sid, [])
            if not samples:
                continue
            n_samp = len(samples)
            observable = [s for s in samples if s.is_observable()]
            frac_obs = len(observable) / n_samp
            if frac_obs < min_usable_sample_frac:
                continue

            usable_ids.append(sid)
            usable_span_sec = max(
                usable_span_sec, n_samp * float(sample_interval_sec)
            )

            aligned_flags: List[bool] = []
            head_down_count = 0
            prev_hand = False
            for s in observable:
                al = sample_aligned(
                    s,
                    teaching_mode=mode,
                    yaw_threshold_deg=yaw_threshold_deg,
                    tier1_yaw_threshold_deg=tier1_yaw_threshold_deg,
                    respect_teaching_modes=respect_teaching_modes,
                )
                if al is None:
                    continue
                aligned_flags.append(al)
                if s.head_down_cue:
                    head_down_count += 1
                # Discrete raises (rising edge), not per-frame detections
                if s.hand_raised and not prev_hand:
                    hand_raise_events += 1
                prev_hand = bool(s.hand_raised)
                if al:
                    dominant_counts["target_oriented"] += 1
                elif s.head_down_cue:
                    dominant_counts["head_down"] += 1
                else:
                    dominant_counts["yaw_away"] += 1

            if aligned_flags:
                o_rates.append(sum(1 for a in aligned_flags if a) / len(aligned_flags))

            hd_sec = head_down_count * float(sample_interval_sec)
            if hd_sec >= head_down_min_seconds:
                head_down_sustained += 1

        n_usable = len(usable_ids)
        coverage = 100.0 * n_usable / expected_n if expected_n else 0.0
        partial = usable_span_sec < partial_window_min_seconds
        low_cov = coverage < min_coverage_pct or n_usable < min_usable_seats

        quality: Optional[str] = None
        if low_cov:
            quality = "insufficient_coverage"
        elif partial:
            quality = "partial_window"

        ttoi: Optional[float] = None
        ttoi_lo: Optional[float] = None
        ttoi_hi: Optional[float] = None
        if o_rates and not low_cov:
            mean_o = sum(o_rates) / len(o_rates)
            ttoi = round(100.0 * mean_o, 1)
            lo, hi = _bootstrap_ci(
                [100.0 * x for x in o_rates],
                iters=bootstrap_iters,
                seed=i * 17 + expected_n,
            )
            ttoi_lo = round(max(0.0, lo), 1)
            ttoi_hi = round(min(100.0, hi), 1)

        hdc = (
            round(100.0 * head_down_sustained / n_usable, 1) if n_usable else 0.0
        )
        if dominant_counts:
            dominant_cue = max(dominant_counts.items(), key=lambda kv: kv[1])[0]
        else:
            dominant_cue = None

        windows.append(
            {
                "start_sec": float(start),
                "end_sec": float(end),
                "topic_id": topic_id,
                "teaching_mode": mode,
                "expected_regions": expected_n,
                "usable_regions": n_usable,
                "coverage_pct": round(coverage, 1),
                "ttoi": ttoi,
                "ttoi_lo": ttoi_lo,
                "ttoi_hi": ttoi_hi,
                "head_down_cue_pct": hdc,
                "hand_raise_events": int(hand_raise_events),
                "candidate_decline": False,  # filled by drop_events
                "dominant_cue": dominant_cue,
                "data_quality_note": quality,
            }
        )

    return windows
