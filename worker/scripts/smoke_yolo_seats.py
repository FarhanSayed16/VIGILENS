#!/usr/bin/env python3
"""
Phase 17 exit: run YOLOv8-pose, map people → seats, write local debug overlay.

Uses a public Ultralytics sample image with people (not classroom video in git).
Optional: --video path/to.mp4

From repo root:
  $env:PYTHONPATH = "D:\\VIGILENS"
  python worker/scripts/smoke_yolo_seats.py
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

import cv2

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from worker import capture, config, debug_overlay, regions, seat_mapping, vision_yolo


SAMPLE_URL = "https://ultralytics.com/images/bus.jpg"


def _ensure_sample_image(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size > 1000:
        return path
    print(f"Downloading sample image → {path}")
    urllib.request.urlretrieve(SAMPLE_URL, str(path))
    return path


def _seats_for_bus_image() -> list:
    """
    Normalized seat-like regions covering typical person areas in bus.jpg.
    Tuned for Ultralytics bus sample (people standing in lower half).
    """
    return regions.parse_seat_regions(
        [
            {"type": "box", "id": "s1", "x": 0.05, "y": 0.35, "w": 0.22, "h": 0.55},
            {"type": "box", "id": "s2", "x": 0.28, "y": 0.35, "w": 0.22, "h": 0.55},
            {"type": "box", "id": "s3", "x": 0.52, "y": 0.35, "w": 0.22, "h": 0.55},
            {"type": "box", "id": "s4", "x": 0.74, "y": 0.35, "w": 0.22, "h": 0.55},
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 17 YOLO + seat smoke")
    parser.add_argument("--video", type=str, default="", help="Optional MP4 path")
    parser.add_argument(
        "--weights",
        type=str,
        default="",
        help="Override YOLO weights (default from configs/default.yaml)",
    )
    parser.add_argument("--max-frames", type=int, default=8)
    args = parser.parse_args()

    cfg = config.load_config()
    weights = args.weights or (cfg.get("models") or {}).get(
        "yolo_pose_weights", "yolov8n-pose.pt"
    )
    occ_frac = float(
        (cfg.get("calibration") or {}).get("occupied_seat_min_fraction", 0.5)
    )

    out_dir = REPO / "uploads" / "_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)

    model = vision_yolo.load_yolo_pose(weights)
    print(f"loaded model weights={weights}")

    seats = _seats_for_bus_image()
    frame_maps = []
    debug_frames = []

    if args.video:
        source = Path(args.video)
        if not source.is_file():
            print(f"ERROR: video not found: {source}", file=sys.stderr)
            return 1
        samples = list(
            capture.iter_sampled_frames(
                source,
                sample_fps=config.sampling_fps(cfg),
                max_frames=args.max_frames,
            )
        )
        print(f"video samples={len(samples)} from {source}")
    else:
        img_path = _ensure_sample_image(out_dir / "bus.jpg")
        img = cv2.imread(str(img_path))
        if img is None:
            print("ERROR: could not read sample image", file=sys.stderr)
            return 1
        # Treat still as a short scripted clip (repeat) for calibration
        samples = []
        for i in range(min(args.max_frames, 5)):
            samples.append(
                capture.SampledFrame(
                    index=i,
                    frame_index=i,
                    time_sec=float(i) / max(config.sampling_fps(cfg), 0.1),
                    image=img.copy(),
                    width=img.shape[1],
                    height=img.shape[0],
                )
            )
        print(f"scripted still frames={len(samples)} from {img_path}")

    total_people = 0
    for s in samples:
        people = vision_yolo.detect_persons(model, s.image, conf=0.25)
        total_people += len(people)
        fmap = seat_mapping.assign_persons_to_seats(
            people,
            seats,
            frame_width=s.width,
            frame_height=s.height,
            time_sec=s.time_sec,
        )
        frame_maps.append(fmap)
        assigned = sum(1 for p in fmap.persons if p.seat_id)
        print(
            f"t={s.time_sec:.2f}s people={len(people)} assigned={assigned} "
            f"unassigned={len(fmap.unassigned_indices)}"
        )

    if total_people == 0:
        print(
            "ERROR: YOLO found 0 people — check weights/network/sample",
            file=sys.stderr,
        )
        return 1

    calib = seat_mapping.calibrate_occupancy(
        frame_maps, seats, occupied_seat_min_fraction=occ_frac
    )
    print(
        f"calibration: n_frames={calib.n_frames} N_expected={calib.n_expected} "
        f"occupied={calib.occupied_seat_ids}"
    )
    print(f"fractions={calib.seat_occupancy_fraction}")

    # Overlay last frame + short debug video
    last = samples[-1]
    last_map = frame_maps[-1]
    overlay = debug_overlay.compose_debug_frame(
        last.image,
        seats,
        last_map,
        calibration=calib,
        title="Phase17 YOLO+seats",
    )
    png = debug_overlay.write_debug_image(out_dir / "phase17_seats_overlay.png", overlay)
    print(f"wrote overlay: {png}")

    for s, fm in zip(samples, frame_maps):
        debug_frames.append(
            debug_overlay.compose_debug_frame(
                s.image, seats, fm, calibration=calib, title="Phase17"
            )
        )
    mp4 = debug_overlay.write_debug_video(
        out_dir / "phase17_seats_debug.mp4",
        debug_frames,
        fps=max(1.0, config.sampling_fps(cfg)),
    )
    print(f"wrote debug video: {mp4}")

    seats_with_det = [
        sid for sid, idxs in last_map.seat_to_person_indices.items() if idxs
    ]
    if not seats_with_det and calib.n_expected == 0:
        print(
            "ERROR: no seat received a detection (adjust seat boxes or sample)",
            file=sys.stderr,
        )
        return 1

    print("Phase 17 smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
