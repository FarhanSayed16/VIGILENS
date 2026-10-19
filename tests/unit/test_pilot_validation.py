"""Phase 22 — decline comparison ±30s fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from worker.pilot_validation import (
    TimeSpan,
    compare_declines,
    load_human_marks_csv,
    validate_annotation_labels,
)


def test_match_within_30s():
    machine = [TimeSpan(300, 360, label="yaw_away")]
    human = [TimeSpan(320, 340, label="orientation_decline")]
    r = compare_declines(machine, human, tolerance_sec=30.0)
    assert r.true_positives == 1
    assert r.false_positives == 0
    assert r.false_negatives == 0


def test_miss_outside_tolerance():
    machine = [TimeSpan(100, 130)]
    human = [TimeSpan(200, 230)]
    r = compare_declines(machine, human, tolerance_sec=30.0)
    assert r.true_positives == 0
    assert r.false_positives == 1
    assert r.false_negatives == 1


def test_emotion_label_warning():
    spans = [TimeSpan(0, 10, label="students_bored")]
    warns = validate_annotation_labels(spans)
    assert warns


def test_load_example_csv():
    path = REPO / "tests" / "fixtures" / "pilot" / "human_marks_example.csv"
    rows = load_human_marks_csv(path)
    assert len(rows) == 1
    assert rows[0].label == "orientation_decline"
