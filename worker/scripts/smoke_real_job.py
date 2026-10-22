#!/usr/bin/env python3
"""
Phase 20 / Checkpoint B offline: run_real_job on a short clip → schema JSON.

Builds a few-second MP4 from Ultralytics bus.jpg (people present), runs YOLO
(+ MediaPipe when faces large enough), writes windows/events JSON.

From repo root:
  $env:PYTHONPATH = "D:\\VIGILENS;D:\\VIGILENS\\backend"
  python worker/scripts/smoke_real_job.py
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

import cv2

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
BACKEND = REPO / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from worker.fake_worker import JobContract
from worker.jobs import run_real_job

SAMPLE_URL = "https://ultralytics.com/images/bus.jpg"


def _ensure_bus(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size > 1000:
        return path
    print(f"Downloading sample -> {path}")
    req = urllib.request.Request(SAMPLE_URL, headers={"User-Agent": "VIGILENS-smoke/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        path.write_bytes(resp.read())
    return path


def _write_clip_from_image(img_path: Path, out_mp4: Path, *, n_frames: int = 12, fps: float = 2.0) -> Path:
    img = cv2.imread(str(img_path))
    if img is None:
        raise RuntimeError(f"Could not read {img_path}")
    h, w = img.shape[:2]
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_mp4), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"VideoWriter failed for {out_mp4}")
    try:
        for i in range(n_frames):
            frame = img.copy()
            cv2.putText(
                frame,
                f"phase20 t={i / fps:.1f}s",
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (240, 240, 240),
                2,
                cv2.LINE_AA,
            )
            writer.write(frame)
    finally:
        writer.release()
    return out_mp4.resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 20 real job smoke")
    parser.add_argument("--video", type=str, default="", help="Optional existing MP4")
    parser.add_argument("--max-frames", type=int, default=8)
    args = parser.parse_args()

    out_dir = REPO / "uploads" / "_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.video:
        video = Path(args.video)
        if not video.is_file():
            print(f"ERROR: video not found: {video}", file=sys.stderr)
            return 1
    else:
        bus = _ensure_bus(out_dir / "bus.jpg")
        video = _write_clip_from_image(bus, out_dir / "phase20_bus_clip.mp4")
        print(f"wrote clip: {video}")

    seats = [
        {"type": "box", "id": "s1", "x": 0.05, "y": 0.35, "w": 0.22, "h": 0.55},
        {"type": "box", "id": "s2", "x": 0.28, "y": 0.35, "w": 0.22, "h": 0.55},
        {"type": "box", "id": "s3", "x": 0.52, "y": 0.35, "w": 0.22, "h": 0.55},
        {"type": "box", "id": "s4", "x": 0.74, "y": 0.35, "w": 0.22, "h": 0.55},
    ]

    stages: list[str] = []

    def on_progress(pct: float, stage: str) -> None:
        stages.append(f"{stage}:{pct:.0f}")
        print(f"  progress {pct:5.1f}%  {stage}")

    contract = JobContract(
        session_id=20,
        job_id=1,
        source_type="upload",
        video_path=str(video),
        seat_count=len(seats),
        seat_regions=seats,
        target_roi={"type": "box", "id": "board", "x": 0.3, "y": 0.0, "w": 0.4, "h": 0.2},
        topics=[{"id": 1, "start_sec": 0.0, "end_sec": 60.0, "label": "Demo"}],
        modes=[{"mode": "explanation", "start_sec": 0.0}],
        duration_sec=30.0,
    )

    raw = run_real_job(
        contract,
        on_progress=on_progress,
        max_frames=args.max_frames,
    )

    from app.schemas.results import WorkerResultPayload

    payload = WorkerResultPayload.model_validate(raw)
    out_json = out_dir / "phase20_real_job.json"
    out_json.write_text(
        json.dumps(payload.model_dump(), indent=2),
        encoding="utf-8",
    )
    print(f"wrote {out_json}")
    print(
        f"windows={len(payload.windows)} events={len(payload.events)} "
        f"stages={len(stages)}"
    )
    if not payload.windows:
        print("ERROR: expected windows from real job", file=sys.stderr)
        return 1
    if "vision" not in " ".join(stages):
        print("ERROR: expected vision progress stage", file=sys.stderr)
        return 1

    # Honesty: short clips with few seats often mark insufficient_coverage
    notes = {w.data_quality_note for w in payload.windows}
    print(f"quality_notes={notes}")
    declines = sum(1 for w in payload.windows if w.candidate_decline)
    print(f"candidate_decline_windows={declines} (suppressed when coverage low)")

    print("Phase 20 smoke OK (real worker → WorkerResultPayload)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
