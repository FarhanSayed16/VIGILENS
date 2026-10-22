#!/usr/bin/env python3
"""
Phase 22 — pilot validation dry-run (no classroom video in git).

Exercises:
  1) Offline TTOI fixture with a mid-lecture decline (same as Phase 19)
  2) Synthetic human marks aligned / offset for ±30s matching
  3) Writes pilot report stub + confirms purge default in config

Does NOT claim a real institutional lecture was analysed.
Operator completes the real lecture via docs/PILOT_RUNBOOK.md.

From repo root:
  $env:PYTHONPATH = "D:\\VIGILENS;D:\\VIGILENS\\backend"
  python worker/scripts/pilot_dry_run.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
BACKEND = REPO / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from worker import config, jobs
from worker.fake_worker import JobContract
from worker.pilot_validation import (
    compare_declines,
    events_to_spans,
    load_human_marks_csv,
    validate_annotation_labels,
)


def main() -> int:
    out_dir = REPO / "uploads" / "_smoke"
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = config.load_config()
    privacy = cfg.get("privacy") or {}
    if not privacy.get("purge_video_after_analysis", True):
        print(
            "ERROR: pilot default requires purge_video_after_analysis=true",
            file=sys.stderr,
        )
        return 1

    seats = [f"s{i+1}" for i in range(8)]
    contract = JobContract(
        session_id=22,
        job_id=1,
        source_type="upload",
        seat_count=len(seats),
        seat_regions=[
            {
                "type": "box",
                "id": sid,
                "x": (i % 4) * 0.24,
                "y": 0.3,
                "w": 0.22,
                "h": 0.5,
            }
            for i, sid in enumerate(seats)
        ],
        topics=[
            {"id": 1, "start_sec": 0.0, "end_sec": 300.0, "label": "Intro"},
            {"id": 2, "start_sec": 300.0, "end_sec": 600.0, "label": "Core"},
        ],
        modes=[
            {"mode": "explanation", "start_sec": 0.0},
            {"mode": "note_taking", "start_sec": 180.0},
            {"mode": "explanation", "start_sec": 240.0},
        ],
        duration_sec=600.0,
    )

    payload = jobs.run_offline_metrics(contract)
    from app.schemas.results import WorkerResultPayload

    WorkerResultPayload.model_validate(payload)

    machine_path = out_dir / "phase22_machine_events.json"
    machine_path.write_text(
        json.dumps({"events": payload["events"], "windows": payload["windows"]}, indent=2),
        encoding="utf-8",
    )

    # Synthetic human marks: match first machine event mid ±10s if any, else invent
    human_csv = out_dir / "phase22_human_marks.csv"
    events = payload["events"]
    with human_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=["start_sec", "end_sec", "label", "note"]
        )
        w.writeheader()
        if events:
            e0 = events[0]
            mid = 0.5 * (float(e0["start_sec"]) + float(e0["end_sec"]))
            w.writerow(
                {
                    "start_sec": round(mid - 15, 1),
                    "end_sec": round(mid + 20, 1),
                    "label": "orientation_decline",
                    "note": "Visible class yaw-away cluster (dry-run mark)",
                }
            )
        else:
            # Fixture should produce a decline; if not, still exercise FN path
            w.writerow(
                {
                    "start_sec": 300.0,
                    "end_sec": 360.0,
                    "label": "orientation_decline",
                    "note": "Dry-run expected dip region",
                }
            )

    human = load_human_marks_csv(human_csv)
    for warn in validate_annotation_labels(human):
        print(f"WARN  {warn}", file=sys.stderr)

    comp = compare_declines(
        events_to_spans(events),
        human,
        tolerance_sec=30.0,
    )
    report = {
        "kind": "pilot_dry_run",
        "consent_reminder": (
            "Use only lectures under existing institutional/student consent. "
            "Do not commit classroom video to git."
        ),
        "purge_video_after_analysis": True,
        "machine_windows": len(payload["windows"]),
        "machine_events": len(events),
        "comparison": comp.to_dict(),
        "runbook": "docs/PILOT_RUNBOOK.md",
        "limitations": "docs/PILOT_LIMITATIONS.md",
        "real_lecture_complete": False,
        "note": (
            "Dry-run only. Record the first consented lecture in "
            "docs/PILOT_SESSION.md after running through the app."
        ),
    }
    out_json = out_dir / "phase22_pilot_dry_run.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote {machine_path}")
    print(f"wrote {human_csv}")
    print(f"wrote {out_json}")
    print(
        f"comparison TP={comp.true_positives} FP={comp.false_positives} "
        f"FN={comp.false_negatives} precision={comp.precision} recall={comp.recall}"
    )
    if events and comp.true_positives < 1:
        print("ERROR: expected ≥1 matched decline in dry-run", file=sys.stderr)
        return 1
    print("Phase 22 dry-run OK (tooling path; real lecture is operator step)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
