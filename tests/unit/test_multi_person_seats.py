"""Multi-person / classroom seat assignment."""

import numpy as np

from worker.regions import parse_seat_regions
from worker.seat_mapping import assign_persons_to_seats, dedupe_persons
from worker.vision_yolo import PersonDetection


def _person(x1, y1, x2, y2, conf=0.9) -> PersonDetection:
    kps = np.zeros((17, 3), dtype=np.float32)
    # mid-hip approx
    kps[11] = [(x1 + x2) / 2, y2 - 10, 0.9]
    kps[12] = [(x1 + x2) / 2, y2 - 10, 0.9]
    return PersonDetection(
        bbox_xyxy=(float(x1), float(y1), float(x2), float(y2)),
        conf=float(conf),
        keypoints=kps,
    )


def test_people_outside_drawn_seats_stay_unassigned():
    seats = parse_seat_regions(
        [{"type": "box", "id": "s1", "x": 0.05, "y": 0.2, "w": 0.2, "h": 0.5}]
    )
    people = [
        _person(80, 100, 220, 500, 0.95),  # in s1
        _person(400, 120, 560, 520, 0.9),
        _person(700, 110, 860, 510, 0.88),
        _person(950, 130, 1100, 530, 0.85),
    ]
    fmap = assign_persons_to_seats(
        people,
        seats,
        frame_width=1280,
        frame_height=720,
        time_sec=1.0,
        virtual_for_unassigned=True,
    )
    assert fmap.seat_to_person_indices["s1"]
    assert "v1" not in fmap.seat_to_person_indices
    assert len(fmap.unassigned_indices) == 3


def test_dedupe_overlaps():
    a = _person(100, 100, 300, 400, 0.99)
    b = _person(110, 110, 310, 410, 0.5)
    kept = dedupe_persons([a, b])
    assert len(kept) == 1
    assert kept[0].conf == 0.99
