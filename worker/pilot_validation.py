"""
Pilot validation helpers (Phase 22).

Human annotators mark *visible orientation* changes / declines — not emotion.
Compare machine candidate declines to human marks with ±tolerance seconds.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union


@dataclass
class TimeSpan:
    start_sec: float
    end_sec: float
    label: Optional[str] = None
    note: Optional[str] = None

    @property
    def mid_sec(self) -> float:
        return 0.5 * (self.start_sec + self.end_sec)


def load_human_marks_csv(path: Union[str, Path]) -> List[TimeSpan]:
    """
    CSV columns (header required):
      start_sec, end_sec [, label, note]

    label examples: orientation_decline | visible_yaw_away | head_down_cluster
    Do NOT use emotion labels (bored, distracted, lazy, …).
    """
    path = Path(path)
    rows: List[TimeSpan] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "start_sec" not in reader.fieldnames:
            raise ValueError("CSV must have start_sec (and usually end_sec) columns")
        for raw in reader:
            if not raw.get("start_sec"):
                continue
            start = float(raw["start_sec"])
            end = float(raw["end_sec"]) if raw.get("end_sec") not in (None, "") else start
            if end < start:
                start, end = end, start
            label = (raw.get("label") or "").strip() or None
            note = (raw.get("note") or "").strip() or None
            rows.append(TimeSpan(start_sec=start, end_sec=end, label=label, note=note))
    return rows


def events_to_spans(events: Sequence[Dict[str, Any]]) -> List[TimeSpan]:
    out: List[TimeSpan] = []
    for e in events:
        out.append(
            TimeSpan(
                start_sec=float(e["start_sec"]),
                end_sec=float(e["end_sec"]),
                label=str(e.get("dominant_cue") or "candidate_decline"),
                note=e.get("note"),
            )
        )
    return out


def _overlap(a: TimeSpan, b: TimeSpan) -> bool:
    return a.start_sec <= b.end_sec and b.start_sec <= a.end_sec


def _within_tolerance(a: TimeSpan, b: TimeSpan, tol_sec: float) -> bool:
    """True if midpoints within tol OR intervals overlap when expanded by tol."""
    if abs(a.mid_sec - b.mid_sec) <= tol_sec:
        return True
    expanded = TimeSpan(a.start_sec - tol_sec, a.end_sec + tol_sec)
    return _overlap(expanded, b)


@dataclass
class DeclineComparison:
    tolerance_sec: float
    machine_count: int
    human_count: int
    true_positives: int
    false_positives: int
    false_negatives: int
    matched_pairs: List[Dict[str, Any]]
    unmatched_machine: List[TimeSpan]
    unmatched_human: List[TimeSpan]

    @property
    def precision(self) -> Optional[float]:
        denom = self.true_positives + self.false_positives
        return (self.true_positives / denom) if denom else None

    @property
    def recall(self) -> Optional[float]:
        denom = self.true_positives + self.false_negatives
        return (self.true_positives / denom) if denom else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tolerance_sec": self.tolerance_sec,
            "machine_count": self.machine_count,
            "human_count": self.human_count,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": None if self.precision is None else round(self.precision, 3),
            "recall": None if self.recall is None else round(self.recall, 3),
            "matched_pairs": self.matched_pairs,
            "unmatched_machine": [
                {"start_sec": s.start_sec, "end_sec": s.end_sec, "label": s.label}
                for s in self.unmatched_machine
            ],
            "unmatched_human": [
                {"start_sec": s.start_sec, "end_sec": s.end_sec, "label": s.label}
                for s in self.unmatched_human
            ],
        }


def compare_declines(
    machine: Sequence[TimeSpan],
    human: Sequence[TimeSpan],
    *,
    tolerance_sec: float = 30.0,
) -> DeclineComparison:
    """
    Greedy 1:1 match: each machine event pairs with nearest unmatched human
    mark within ±tolerance_sec (midpoint / expanded overlap).
    """
    m_list = list(machine)
    h_list = list(human)
    used_h = set()
    matched: List[Dict[str, Any]] = []

    # Prefer matching by midpoint distance
    candidates = []
    for i, m in enumerate(m_list):
        for j, h in enumerate(h_list):
            if _within_tolerance(m, h, tolerance_sec):
                dist = abs(m.mid_sec - h.mid_sec)
                candidates.append((dist, i, j))
    candidates.sort()

    used_m = set()
    for dist, i, j in candidates:
        if i in used_m or j in used_h:
            continue
        used_m.add(i)
        used_h.add(j)
        m, h = m_list[i], h_list[j]
        matched.append(
            {
                "machine": {"start_sec": m.start_sec, "end_sec": m.end_sec},
                "human": {"start_sec": h.start_sec, "end_sec": h.end_sec, "label": h.label},
                "midpoint_delta_sec": round(dist, 2),
            }
        )

    unmatched_m = [m_list[i] for i in range(len(m_list)) if i not in used_m]
    unmatched_h = [h_list[j] for j in range(len(h_list)) if j not in used_h]
    tp = len(matched)
    return DeclineComparison(
        tolerance_sec=tolerance_sec,
        machine_count=len(m_list),
        human_count=len(h_list),
        true_positives=tp,
        false_positives=len(unmatched_m),
        false_negatives=len(unmatched_h),
        matched_pairs=matched,
        unmatched_machine=unmatched_m,
        unmatched_human=unmatched_h,
    )


FORBIDDEN_EMOTION_LABELS = frozenset(
    {
        "bored",
        "boredom",
        "lazy",
        "distracted",
        "attention",
        "inattentive",
        "engaged",
        "engagement",
        "happy",
        "sad",
        "angry",
    }
)


def validate_annotation_labels(spans: Iterable[TimeSpan]) -> List[str]:
    """Return warnings if labels look like emotion / attention judgments."""
    warnings: List[str] = []
    for s in spans:
        if not s.label:
            continue
        key = s.label.strip().lower().replace(" ", "_")
        for bad in FORBIDDEN_EMOTION_LABELS:
            if bad in key:
                warnings.append(
                    f"label '{s.label}' looks like emotion/attention — "
                    "use visible orientation only (e.g. orientation_decline)"
                )
                break
    return warnings
