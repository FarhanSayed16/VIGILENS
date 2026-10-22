#!/usr/bin/env python3
"""
Phase 16 exit criteria: print frame count / sample timestamps from a test clip.

Usage (from repo root):
  set PYTHONPATH=.
  python worker/scripts/smoke_capture.py

Optional:
  python worker/scripts/smoke_capture.py --video path/to.mp4
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root on path
REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from worker import capture, config, regions  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="VIGILENS Phase 16 capture smoke")
    parser.add_argument(
        "--video",
        type=str,
        default="",
        help="MP4 path (default: write synthetic clip under uploads/_smoke/)",
    )
    parser.add_argument("--max-frames", type=int, default=20)
    args = parser.parse_args()

    cfg = config.load_config()
    fps = config.sampling_fps(cfg)
    print(f"config: {config.DEFAULT_CONFIG_PATH}")
    print(f"version={cfg.get('version')} sample_fps={fps}")
    print(
        f"yaw_threshold_deg={config.yaw_threshold_deg(cfg)} "
        f"face_width_min_px={config.face_width_min_px(cfg)}"
    )

    if args.video:
        video_path = Path(args.video)
    else:
        video_path = REPO / "uploads" / "_smoke" / "phase16_synthetic.mp4"
        capture.write_synthetic_clip(video_path, duration_sec=4.0, fps=10.0)
        print(f"wrote synthetic clip: {video_path}")

    info = capture.probe_source(video_path)
    print(
        f"probe: kind={info.source_kind} native_fps={info.fps_native:.2f} "
        f"frames={info.frame_count} size={info.width}x{info.height}"
    )

    samples = list(
        capture.iter_sampled_frames(
            video_path, sample_fps=fps, max_frames=args.max_frames
        )
    )
    print(f"sampled_count={len(samples)}")
    print("sample_timestamps_sec=" + ", ".join(f"{s.time_sec:.3f}" for s in samples))

    # Geometry helpers smoke (normalized room layout)
    seats = regions.parse_seat_regions(
        [
            {"type": "box", "id": "s1", "x": 0.1, "y": 0.4, "w": 0.2, "h": 0.25},
            {"type": "box", "id": "s2", "x": 0.4, "y": 0.4, "w": 0.2, "h": 0.25},
            {
                "type": "polygon",
                "id": "s3",
                "points": [[0.7, 0.4], [0.9, 0.4], [0.9, 0.7], [0.7, 0.7]],
            },
        ]
    )
    target = regions.parse_target(
        {"type": "box", "id": "board", "x": 0.35, "y": 0.02, "w": 0.3, "h": 0.15}
    )
    assert target is not None
    geom = regions.teaching_target_geometry(target, seats)
    print(
        f"geometry: seats={len(seats)} target_centroid={geom.centroid_norm} "
        f"facing={geom.facing_vector_norm}"
    )
    # Person at seat s1 center → assigned
    cx, cy = seats[0].centroid_norm()
    sid = regions.assign_point_to_seat(cx, cy, seats)
    print(f"assign_centroid_s1 -> {sid}")
    yaw_p = regions.yaw_relative_to_target_deg(0.0, facing_vector_norm=geom.facing_vector_norm)
    print(
        f"yaw_prime_at_0={yaw_p:.1f} target_oriented="
        f"{regions.is_target_oriented(yaw_p, yaw_threshold_deg=config.yaw_threshold_deg(cfg))}"
    )

    if len(samples) < 2:
        print("ERROR: expected at least 2 sampled frames", file=sys.stderr)
        return 1
    print("Phase 16 smoke OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
