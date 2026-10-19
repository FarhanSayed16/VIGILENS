"""Solo-seat assignment fallback for live desk testing."""

import numpy as np

from worker.regions import parse_seat_regions
from worker.seat_mapping import assign_persons_to_seats
from worker.vision_yolo import PersonDetection


def test_solo_seat_claims_unassigned_person():
    seats = parse_seat_regions(
        [{"type": "box", "id": "s1", "x": 0.8, "y": 0.8, "w": 0.15, "h": 0.15}]
    )
    # Person in center — outside the corner seat box
    kps = np.zeros((17, 3), dtype=np.float32)
    person = PersonDetection(
        bbox_xyxy=(400.0, 300.0, 600.0, 700.0),
        conf=0.9,
        keypoints=kps,
    )
    fmap = assign_persons_to_seats(
        [person], seats, frame_width=1280, frame_height=720, time_sec=1.0
    )
    assert fmap.seat_to_person_indices["s1"] == [0]
    assert person.seat_id == "s1"
