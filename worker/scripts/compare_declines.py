#!/usr/bin/env python3
"""
Phase 22 — compare machine candidate declines vs human marks (±30s default).

Human CSV: start_sec,end_sec,label,note
Machine: JSON ({events:[...]} or list) OR CSV with start_sec,end_sec[,label]

From repo root:
  $env:PYTHONPATH = "D:\\VIGILENS"
  python worker/scripts/compare_declines.py --human marks.csv --machine events.json
  python worker/scripts/compare_declines.py --human marks.csv --machine events.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from worker.pilot_validation import (
    compare_declines,
    events_to_spans,
    load_human_marks_csv,
    validate_annotation_labels,
)


def _load_machine_events(path: Path) -> list:
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _events_from_csv(text)
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "events" in data:
            return data["events"]
        # GET /sessions/{id}/events → { items, total, session_id }
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
    raise ValueError(
        "Machine JSON must be a list of events, {events: [...]}, or API {items: [...]}"
    )


def _events_from_csv(text: str) -> list:
    """
    Accept a simple events CSV or a VIGILENS export with '# EVENTS' section.
    """
    lines = text.splitlines()
    start_idx = 0
    for i, line in enumerate(lines):
        low = line.lower().strip()
        if low.startswith("#") and "event" in low:
            start_idx = i + 1
            break
    # Header is next non-empty line
    while start_idx < len(lines) and not lines[start_idx].strip():
        start_idx += 1
    chunk = lines[start_idx:]
    # Stop at next # section
    end = len(chunk)
    for j, line in enumerate(chunk):
        if j > 0 and line.strip().startswith("#"):
            end = j
            break
    reader = csv.DictReader(chunk[:end])
    if not reader.fieldnames or "start_sec" not in reader.fieldnames:
        reader = csv.DictReader(lines)
    if not reader.fieldnames or "start_sec" not in (reader.fieldnames or []):
        raise ValueError("Machine CSV needs start_sec (and usually end_sec) columns")
    events = []
    for raw in reader:
        if not raw.get("start_sec"):
            continue
        # Prefer event rows (have depth); skip window rows from mis-sliced exports
        if "depth" in (reader.fieldnames or []) and raw.get("depth") in (None, ""):
            if raw.get("ttoi") not in (None, ""):
                continue
        start = float(raw["start_sec"])
        end_sec = float(raw["end_sec"]) if raw.get("end_sec") not in (None, "") else start
        events.append(
            {
                "start_sec": start,
                "end_sec": end_sec,
                "depth": float(raw["depth"]) if raw.get("depth") not in (None, "") else 0.0,
                "dominant_cue": raw.get("dominant_cue") or raw.get("label"),
                "note": raw.get("note"),
            }
        )
    return events


def main() -> int:
    p = argparse.ArgumentParser(description="Compare declines ±tolerance")
    p.add_argument("--human", required=True, help="Human marks CSV")
    p.add_argument("--machine", required=True, help="Machine events JSON or CSV")
    p.add_argument("--tolerance", type=float, default=30.0)
    p.add_argument("--out", type=str, default="", help="Write comparison JSON")
    args = p.parse_args()

    human = load_human_marks_csv(args.human)
    warns = validate_annotation_labels(human)
    for w in warns:
        print(f"WARN  {w}", file=sys.stderr)

    machine = events_to_spans(_load_machine_events(Path(args.machine)))
    result = compare_declines(machine, human, tolerance_sec=args.tolerance)
    report = result.to_dict()
    print(json.dumps(report, indent=2))

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"wrote {out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
