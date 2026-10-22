#!/usr/bin/env python3
"""
Phase 21 — scripted behaviour threshold evaluation (no classroom video required).

Behaviours:
  face_board / turn_away / head_down / hand_raise
  note_taking head-down ≠ failure
  far seat → Tier-1 or unobservable (no invented Tier-2)

From repo root:
  $env:PYTHONPATH = "D:\\VIGILENS;D:\\VIGILENS\\backend"
  python worker/scripts/eval_thresholds.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
BACKEND = REPO / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from worker import aggregation, config, metrics_pipeline, vision_mediapipe
from worker.features import (
    SeatFrameFeature,
    fuse_seat_feature,
    sample_aligned,
)
from worker.vision_yolo import PersonDetection

FACE_URL = (
    "https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/lena.jpg"
)


def _feat(
    seat: str,
    t: float,
    *,
    yaw: float,
    pitch: float = 5.0,
    head_down: bool = False,
    hand: bool = False,
    tier: int = 2,
) -> SeatFrameFeature:
    return SeatFrameFeature(
        seat_id=seat,
        time_sec=t,
        occupied=True,
        target_oriented=None,
        yaw_prime_deg=yaw,
        pitch_deg=pitch,
        head_down_cue=head_down,
        hand_raised=hand,
        tier=tier,
        person_conf=0.9,
    )


def _timeline(
    behaviour: str,
    seats: List[str],
    *,
    duration: float = 30.0,
    dt: float = 1.0,
) -> Tuple[List[SeatFrameFeature], Dict[str, Any]]:
    """Build one 30s window of scripted seat features."""
    feats: List[SeatFrameFeature] = []
    t = 0.0
    while t < duration - 1e-9:
        for sid in seats:
            if behaviour == "face_board":
                feats.append(_feat(sid, t, yaw=8.0, pitch=5.0))
            elif behaviour == "turn_away":
                feats.append(_feat(sid, t, yaw=48.0, pitch=5.0))
            elif behaviour == "head_down":
                feats.append(
                    _feat(sid, t, yaw=10.0, pitch=28.0, head_down=True)
                )
            elif behaviour == "hand_raise":
                feats.append(_feat(sid, t, yaw=10.0, hand=(sid == seats[0])))
            else:
                raise ValueError(behaviour)
        t += dt
    meta = {"behaviour": behaviour, "seats": len(seats), "duration": duration}
    return feats, meta


def _window_ttoi(
    feats: List[SeatFrameFeature],
    seats: List[str],
    cfg: Dict[str, Any],
    *,
    mode: str = "explanation",
) -> Dict[str, Any]:
    orientation = cfg.get("orientation") or {}
    coverage = cfg.get("coverage") or {}
    sampling = cfg.get("sampling") or {}
    windows = aggregation.aggregate_windows(
        feats,
        expected_seat_ids=seats,
        window_seconds=float(sampling.get("window_seconds", 30)),
        partial_window_min_seconds=1.0,  # scripted full-window samples
        min_usable_sample_frac=float(sampling.get("min_usable_sample_frac", 0.5)),
        min_coverage_pct=float(coverage.get("min_coverage_pct", 70)),
        min_usable_seats=min(int(coverage.get("min_usable_seats", 5)), len(seats)),
        yaw_threshold_deg=float(orientation.get("yaw_threshold_deg", 30)),
        tier1_yaw_threshold_deg=float(
            orientation.get("tier1_yaw_threshold_deg", 45)
        ),
        head_down_min_seconds=float(orientation.get("head_down_min_seconds", 8)),
        modes=[{"mode": mode, "start_sec": 0.0}],
        sample_interval_sec=1.0,
    )
    return windows[0]


def eval_scripted(cfg: Dict[str, Any]) -> List[str]:
    failures: List[str] = []
    seats = [f"s{i}" for i in range(6)]

    # face board → high TTOI
    feats, _ = _timeline("face_board", seats)
    w = _window_ttoi(feats, seats, cfg)
    if w.get("ttoi") is None or w["ttoi"] < 90:
        failures.append(f"face_board: expected high TTOI, got {w.get('ttoi')}")

    # turn away → low TTOI
    feats, _ = _timeline("turn_away", seats)
    w = _window_ttoi(feats, seats, cfg)
    if w.get("ttoi") is None or w["ttoi"] > 15:
        failures.append(f"turn_away: expected low TTOI, got {w.get('ttoi')}")

    # head down (explanation) → low TTOI
    feats, _ = _timeline("head_down", seats)
    w = _window_ttoi(feats, seats, cfg, mode="explanation")
    if w.get("ttoi") is None or w["ttoi"] > 15:
        failures.append(
            f"head_down/explanation: expected low TTOI, got {w.get('ttoi')}"
        )

    # head down (note_taking) → high TTOI (mode hook)
    w = _window_ttoi(feats, seats, cfg, mode="note_taking")
    if w.get("ttoi") is None or w["ttoi"] < 90:
        failures.append(
            f"head_down/note_taking: expected high TTOI, got {w.get('ttoi')}"
        )

    # hand raise counted
    feats, _ = _timeline("hand_raise", seats)
    w = _window_ttoi(feats, seats, cfg)
    if int(w.get("hand_raise_events") or 0) < 1:
        failures.append("hand_raise: expected hand_raise_events ≥ 1")

    # sample_aligned unit checks at thresholds
    yaw_thr = float((cfg.get("orientation") or {}).get("yaw_threshold_deg", 30))
    f_ok = _feat("s1", 0, yaw=yaw_thr - 1, tier=2)
    f_bad = _feat("s1", 0, yaw=yaw_thr + 5, tier=2)
    if sample_aligned(f_ok, yaw_threshold_deg=yaw_thr) is not True:
        failures.append("yaw band: in-band sample should align")
    if sample_aligned(f_bad, yaw_threshold_deg=yaw_thr) is not False:
        failures.append("yaw band: out-of-band sample should not align")

    # Tier-1 wider band
    t1_thr = float(
        (cfg.get("orientation") or {}).get("tier1_yaw_threshold_deg", 45)
    )
    f_t1 = _feat("s1", 0, yaw=35.0, tier=1)
    if sample_aligned(
        f_t1, yaw_threshold_deg=yaw_thr, tier1_yaw_threshold_deg=t1_thr
    ) is not True:
        failures.append("tier1: yaw=35 should align with tier1 band 45")

    return failures


def eval_solvpnp_signs() -> List[str]:
    return vision_mediapipe.verify_solvpnp_sign_convention()


def _ensure_face(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size > 1000:
        return path
    req = urllib.request.Request(FACE_URL, headers={"User-Agent": "VIGILENS-eval/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        path.write_bytes(resp.read())
    return path


def eval_far_seat(cfg: Dict[str, Any], out_dir: Path) -> List[str]:
    """Far / tiny face → no Tier-2; near face → Tier-2 when width ≥ gate."""
    failures: List[str] = []
    face_min = config.face_width_min_px(cfg)
    img_path = _ensure_face(out_dir / "phase21_face.jpg")
    img = cv2.imread(str(img_path))
    if img is None:
        return ["far_seat: could not load face image"]

    try:
        landmarker = vision_mediapipe.load_face_landmarker()
    except Exception as exc:  # noqa: BLE001
        return [f"far_seat: landmarker unavailable ({exc})"]

    # Near: original / upscaled if needed
    near = img
    pose_near = vision_mediapipe.estimate_head_pose(
        landmarker, near, face_width_min_px=face_min
    )
    if pose_near is None:
        near = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        pose_near = vision_mediapipe.estimate_head_pose(
            landmarker, near, face_width_min_px=face_min
        )
    if pose_near is None:
        failures.append("far_seat: near face should pass Tier-2 gate")
    else:
        h, w = near.shape[:2]
        person = PersonDetection(
            bbox_xyxy=(0.0, 0.0, float(w), float(h)),
            conf=0.9,
            keypoints=np.zeros((17, 3), dtype=np.float32),
        )
        person.keypoints[5] = [w * 0.35, h * 0.4, 0.9]
        person.keypoints[6] = [w * 0.65, h * 0.4, 0.9]
        feat = fuse_seat_feature(
            "near",
            0.0,
            person,
            frame_bgr=near,
            landmarker=landmarker,
            face_width_min_px=face_min,
            enable_tier2=True,
        )
        if feat.tier != 2:
            failures.append(f"far_seat: near seat expected tier=2, got {feat.tier}")

    # Far: shrink until face width below gate → Tier-2 returns None
    tiny = cv2.resize(img, None, fx=0.15, fy=0.15, interpolation=cv2.INTER_AREA)
    # Pad back so landmarker can run, but face stays small
    canvas = np.zeros((480, 640, 3), dtype=np.uint8)
    th, tw = tiny.shape[:2]
    y0, x0 = 200, 280
    canvas[y0 : y0 + th, x0 : x0 + tw] = tiny
    pose_far = vision_mediapipe.estimate_head_pose(
        landmarker, canvas, face_width_min_px=face_min
    )
    if pose_far is not None:
        failures.append(
            f"far_seat: tiny face should fail width gate "
            f"(got face_w={pose_far.face_width_px:.0f} ≥ {face_min})"
        )

    # Fuse far person with shoulders → Tier-1 honesty (not invented Tier-2)
    person_far = PersonDetection(
        bbox_xyxy=(float(x0), float(y0), float(x0 + tw), float(y0 + th)),
        conf=0.8,
        keypoints=np.zeros((17, 3), dtype=np.float32),
    )
    person_far.keypoints[5] = [x0 + tw * 0.3, y0 + th * 0.4, 0.9]
    person_far.keypoints[6] = [x0 + tw * 0.7, y0 + th * 0.4, 0.9]
    feat_far = fuse_seat_feature(
        "far",
        0.0,
        person_far,
        frame_bgr=canvas,
        landmarker=landmarker,
        face_width_min_px=face_min,
        enable_tier2=True,
    )
    if feat_far.tier == 2:
        failures.append("far_seat: far seat must not invent Tier-2 precision")
    if feat_far.tier not in (1, None):
        failures.append(f"far_seat: expected tier 1 or unobservable, got {feat_far.tier}")

    return failures


def eval_coverage_gate(cfg: Dict[str, Any]) -> List[str]:
    """Few usable seats → null TTOI, no invented score."""
    failures: List[str] = []
    seats = [f"s{i}" for i in range(10)]
    # Only 2 seats occupied
    feats = []
    for t in range(20):
        for sid in ("s0", "s1"):
            feats.append(_feat(sid, float(t), yaw=5.0))
    coverage = cfg.get("coverage") or {}
    sampling = cfg.get("sampling") or {}
    orientation = cfg.get("orientation") or {}
    windows = aggregation.aggregate_windows(
        feats,
        expected_seat_ids=seats,
        window_seconds=30.0,
        partial_window_min_seconds=1.0,
        min_coverage_pct=float(coverage.get("min_coverage_pct", 70)),
        min_usable_seats=int(coverage.get("min_usable_seats", 5)),
        yaw_threshold_deg=float(orientation.get("yaw_threshold_deg", 30)),
        sample_interval_sec=1.0,
    )
    w = windows[0]
    if w.get("ttoi") is not None:
        failures.append("coverage: low evidence must null TTOI (no invented score)")
    if w.get("data_quality_note") != "insufficient_coverage":
        failures.append(
            f"coverage: expected insufficient_coverage, got {w.get('data_quality_note')}"
        )
    return failures


def main() -> int:
    cfg = config.load_config()
    out_dir = REPO / "uploads" / "_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)

    report: Dict[str, Any] = {
        "config_version": cfg.get("version"),
        "thresholds": {
            "yaw_threshold_deg": config.yaw_threshold_deg(cfg),
            "tier1_yaw_threshold_deg": config.tier1_yaw_threshold_deg(cfg),
            "pitch_down_threshold_deg": config.pitch_down_threshold_deg(cfg),
            "face_width_min_px": config.face_width_min_px(cfg),
            "min_coverage_pct": config.min_coverage_pct(cfg),
            "min_usable_seats": config.min_usable_seats(cfg),
        },
        "checks": {},
        "failures": [],
    }

    sections = [
        ("solvpnp_signs", eval_solvpnp_signs),
        ("scripted_behaviours", lambda: eval_scripted(cfg)),
        ("coverage_honesty", lambda: eval_coverage_gate(cfg)),
        ("far_seat_honesty", lambda: eval_far_seat(cfg, out_dir)),
    ]

    all_fail: List[str] = []
    for name, fn in sections:
        fails = fn()
        report["checks"][name] = "FAIL" if fails else "OK"
        for f in fails:
            all_fail.append(f"{name}: {f}")
            print(f"FAIL  {name}: {f}", file=sys.stderr)
        if not fails:
            print(f"OK    {name}")

    report["failures"] = all_fail
    report["pilot_ready"] = len(all_fail) == 0
    out_json = out_dir / "phase21_threshold_eval.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")

    if all_fail:
        print(f"Phase 21 eval FAILED ({len(all_fail)} checks)", file=sys.stderr)
        return 1
    print("Phase 21 eval OK — thresholds good enough for pilot (scripted)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
