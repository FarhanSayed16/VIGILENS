"""
Fake analysis worker — same output schema as the future real CV worker.

Generates synthetic 30s windows + candidate decline events. No YOLO/MediaPipe.
Invoked by backend job_service (in-process thread for MVP).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


ProgressCb = Callable[[float, str], None]


@dataclass
class JobContract:
    session_id: int
    job_id: int
    source_type: str
    video_path: Optional[str] = None
    source_url: Optional[str] = None
    seat_count: int = 12
    seat_regions: Optional[List[Dict[str, Any]]] = None
    target_roi: Optional[Dict[str, Any]] = None
    # toward_camera = students face lens (board behind camera); no board ROI needed
    facing_mode: Optional[str] = None
    topics: List[Dict[str, Any]] = field(default_factory=list)
    modes: List[Dict[str, Any]] = field(default_factory=list)
    window_seconds: float = 30.0
    duration_sec: float = 600.0  # default 10 min synthetic lecture
    config_version: int = 1


def _active_topic_id(topics: List[Dict[str, Any]], t: float) -> Optional[int]:
    active = None
    for topic in topics:
        start = float(topic.get("start_sec") or 0)
        end = topic.get("end_sec")
        if start <= t and (end is None or float(end) >= t):
            if active is None or start >= float(active.get("start_sec") or 0):
                active = topic
    return int(active["id"]) if active and active.get("id") is not None else None


def _active_mode(modes: List[Dict[str, Any]], t: float) -> Optional[str]:
    chosen = None
    for m in modes:
        if float(m.get("start_sec") or 0) <= t:
            if chosen is None or float(m["start_sec"]) >= float(chosen["start_sec"]):
                chosen = m
    return str(chosen["mode"]) if chosen else "explanation"


def generate_synthetic_results(
    contract: JobContract,
    *,
    on_progress: Optional[ProgressCb] = None,
    rng: Optional[random.Random] = None,
) -> Dict[str, Any]:
    """
    Build windows + events dict matching WorkerResultPayload.
    Calls on_progress(pct, stage) during generation (fast; job_service may throttle).
    """
    rng = rng or random.Random(contract.session_id * 1000 + contract.job_id)
    if on_progress:
        on_progress(8.0, "ingest")

    duration = max(contract.window_seconds, float(contract.duration_sec))
    wlen = float(contract.window_seconds)
    n_windows = max(1, int(math.ceil(duration / wlen)))
    expected = max(1, int(contract.seat_count))

    windows: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []

    if on_progress:
        on_progress(25.0, "vision")

    # Smooth TTOI curve with a mid-lecture dip (candidate decline region)
    dip_center = duration * 0.55
    for i in range(n_windows):
        start = i * wlen
        end = min(duration, start + wlen)
        mid = (start + end) / 2.0

        base = 72.0 + 8.0 * math.sin(mid / 90.0)
        dip = 18.0 * math.exp(-((mid - dip_center) ** 2) / (2 * (80.0**2)))
        noise = rng.uniform(-3.0, 3.0)
        ttoi = max(35.0, min(95.0, base - dip + noise))
        coverage = max(45.0, min(98.0, 82.0 + rng.uniform(-8.0, 8.0) - dip * 0.3))
        usable = max(1, int(round(expected * coverage / 100.0)))

        quality = None
        if coverage < 70.0:
            quality = "insufficient_coverage"
        elif (end - start) < wlen * 0.6:
            quality = "partial_window"

        decline = dip > 10.0 and coverage >= 70.0 and usable >= 5
        mode = _active_mode(contract.modes, mid)
        topic_id = _active_topic_id(contract.topics, mid)

        head_down = 12.0 + (8.0 if mode == "note_taking" else 0.0) + rng.uniform(-2, 4)
        windows.append(
            {
                "start_sec": start,
                "end_sec": end,
                "topic_id": topic_id,
                "teaching_mode": mode,
                "expected_regions": expected,
                "usable_regions": usable,
                "coverage_pct": round(coverage, 1),
                "ttoi": round(ttoi, 1),
                "ttoi_lo": round(max(0.0, ttoi - 6), 1),
                "ttoi_hi": round(min(100.0, ttoi + 6), 1),
                "head_down_cue_pct": round(head_down, 1),
                "hand_raise_events": rng.randint(0, 2) if mode == "qa" else 0,
                "candidate_decline": decline,
                "dominant_cue": "yaw_away" if decline else "target_oriented",
                "data_quality_note": quality,
            }
        )

        if decline and i > 0 and windows[i - 1].get("candidate_decline"):
            # Persist multi-window decline as one event at first occurrence
            if not events or events[-1]["end_sec"] < start - 1:
                events.append(
                    {
                        "start_sec": windows[i - 1]["start_sec"],
                        "end_sec": end,
                        "depth": round(dip + rng.uniform(2, 6), 1),
                        "coverage_pct": round(coverage, 1),
                        "topic_id": topic_id,
                        "teaching_mode": mode,
                        "dominant_cue": "yaw_away",
                        "note": "Candidate orientation decline (synthetic fake worker).",
                    }
                )
            else:
                events[-1]["end_sec"] = end

        if on_progress and i % max(1, n_windows // 5) == 0:
            pct = 25.0 + 45.0 * (i / max(1, n_windows - 1))
            on_progress(pct, "vision")

    # Guarantee at least one candidate decline event for demo realism
    if not events and len(windows) >= 2:
        mid_i = len(windows) // 2
        w0, w1 = windows[mid_i - 1], windows[mid_i]
        w0["candidate_decline"] = True
        w1["candidate_decline"] = True
        w0["dominant_cue"] = "yaw_away"
        w1["dominant_cue"] = "yaw_away"
        events.append(
            {
                "start_sec": w0["start_sec"],
                "end_sec": w1["end_sec"],
                "depth": 12.0,
                "coverage_pct": w1.get("coverage_pct"),
                "topic_id": w1.get("topic_id"),
                "teaching_mode": w1.get("teaching_mode"),
                "dominant_cue": "yaw_away",
                "note": "Candidate orientation decline (synthetic fake worker).",
            }
        )

    if on_progress:
        on_progress(80.0, "aggregate")

    return {"windows": windows, "events": events}


def estimate_duration_sec(
    *,
    video_path: Optional[str],
    topics: List[Dict[str, Any]],
    default: float = 600.0,
) -> float:
    """Heuristic duration when OpenCV probing is not available."""
    if topics:
        ends = []
        for t in topics:
            if t.get("end_sec") is not None:
                ends.append(float(t["end_sec"]))
            ends.append(float(t.get("start_sec") or 0) + 120.0)
        return max(default * 0.5, max(ends))
    if video_path:
        try:
            from pathlib import Path

            size = Path(video_path).stat().st_size
            # ~1 MB/min rough classroom encoding guess, clamp 3–45 min
            minutes = max(3.0, min(45.0, size / (1024 * 1024)))
            return minutes * 60.0
        except OSError:
            pass
    return default
