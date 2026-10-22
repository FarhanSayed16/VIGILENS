#!/usr/bin/env python3
"""
Phase 19 exit: offline TTOI + coverage + declines → JSON matching WorkerResultPayload.

Default: scripted fixture (no GPU). Optional --video runs Tier-1 YOLO features.

From repo root:
  $env:PYTHONPATH = "D:\\VIGILENS"
  python worker/scripts/smoke_ttoi.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BACKEND = REPO / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from worker import config, jobs, metrics_pipeline
from worker.fake_worker import JobContract


def _validate_payload(payload: dict) -> None:
    from app.schemas.results import WorkerResultPayload

    WorkerResultPayload.model_validate(payload)


def _features_from_video(video: Path, seat_ids: list[str], cfg: dict, max_frames: int):
    """Tier-1 only path for optional clip smoke (Phase 20 adds full fuse)."""
    from worker import capture, regions, seat_mapping, vision_yolo
    from worker.features import tier1_features_from_frame_map

    weights = (cfg.get("models") or {}).get("yolo_pose_weights", "yolov8n-pose.pt")
    model = vision_yolo.load_yolo_pose(weights)
    # Spread seats across frame if contract has none
    seats = regions.parse_seat_regions(
        [
            {
                "type": "box",
                "id": sid,
                "x": (i % 4) * 0.24 + 0.02,
                "y": 0.35,
                "w": 0.22,
                "h": 0.55,
            }
            for i, sid in enumerate(seat_ids)
        ]
    )
    feats = []
    for s in capture.iter_sampled_frames(
        video,
        sample_fps=config.sampling_fps(cfg),
        max_frames=max_frames,
    ):
        people = vision_yolo.detect_persons(model, s.image)
        fmap = seat_mapping.assign_persons_to_seats(
            people,
            seats,
            frame_width=s.width,
            frame_height=s.height,
            time_sec=s.time_sec,
        )
        feats.extend(tier1_features_from_frame_map(fmap))
    return feats


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 19 TTOI offline smoke")
    parser.add_argument("--video", type=str, default="", help="Optional MP4 path")
    parser.add_argument("--max-frames", type=int, default=24)
    parser.add_argument("--seats", type=int, default=8)
    parser.add_argument("--duration", type=float, default=600.0)
    args = parser.parse_args()

    cfg = config.load_config()
    out_dir = REPO / "uploads" / "_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)

    seat_ids = [f"s{i+1}" for i in range(max(5, args.seats))]
    contract = JobContract(
        session_id=19,
        job_id=1,
        source_type="upload",
        seat_count=len(seat_ids),
        seat_regions=[
            {
                "type": "box",
                "id": sid,
                "x": (i % 4) * 0.24,
                "y": 0.3,
                "w": 0.22,
                "h": 0.5,
            }
            for i, sid in enumerate(seat_ids)
        ],
        topics=[{"id": 1, "start_sec": 0.0, "end_sec": args.duration, "label": "Topic A"}],
        modes=[
            {"mode": "explanation", "start_sec": 0.0},
            {"mode": "note_taking", "start_sec": 180.0},
            {"mode": "explanation", "start_sec": 240.0},
        ],
        window_seconds=float((cfg.get("sampling") or {}).get("window_seconds", 30)),
        duration_sec=float(args.duration),
    )

    if args.video:
        video = Path(args.video)
        if not video.is_file():
            print(f"ERROR: video not found: {video}", file=sys.stderr)
            return 1
        print(f"extracting Tier-1 features from {video}")
        feats = _features_from_video(video, seat_ids, cfg, args.max_frames)
        if not feats:
            print("ERROR: no features from video", file=sys.stderr)
            return 1
        payload = metrics_pipeline.build_results_from_features(
            feats,
            expected_seat_ids=seat_ids,
            cfg=cfg,
            topics=contract.topics,
            modes=contract.modes,
        )
    else:
        print("building scripted fixture timeline (offline, no GPU)")
        payload = jobs.run_offline_metrics(contract, features=None)

    _validate_payload(payload)
    out_json = out_dir / "phase19_windows_events.json"
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_json}")

    n_w = len(payload["windows"])
    n_e = len(payload["events"])
    with_ttoi = sum(1 for w in payload["windows"] if w.get("ttoi") is not None)
    declines = sum(1 for w in payload["windows"] if w.get("candidate_decline"))
    print(
        f"windows={n_w} with_ttoi={with_ttoi} decline_windows={declines} events={n_e}"
    )
    if n_w < 1:
        print("ERROR: expected at least one window", file=sys.stderr)
        return 1
    if not args.video and n_e < 1:
        print(
            "ERROR: fixture should produce ≥1 candidate decline event",
            file=sys.stderr,
        )
        return 1

    print("Phase 19 smoke OK (schema validated WorkerResultPayload)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
