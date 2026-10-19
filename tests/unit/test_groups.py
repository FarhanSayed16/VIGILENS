"""Anonymous seat clustering (Phase 29)."""

from worker.groups import cluster_low_orientation_seats, groups_to_events


def test_cluster_adjacent_low_seats():
    seats = [
        {"seat_id": "R1C1", "orientation_pct": 30.0, "usable": True},
        {"seat_id": "R1C2", "orientation_pct": 28.0, "usable": True},
        {"seat_id": "R1C3", "orientation_pct": 90.0, "usable": True},
        {"seat_id": "R5C5", "orientation_pct": 20.0, "usable": True},
    ]
    groups = cluster_low_orientation_seats(seats, low_threshold=45.0)
    assert len(groups) >= 1
    labels = {g["label"] for g in groups}
    assert any("Group" in lab for lab in labels)
    # Adjacent R1C1+R1C2 should cluster
    joined = " ".join(" ".join(g["seat_ids"]) for g in groups)
    assert "R1C1" in joined and "R1C2" in joined


def test_groups_to_events():
    groups = [
        {
            "label": "Group A",
            "seat_ids": ["R2C3", "R2C4"],
            "orientation_pct": 35.0,
            "kind": "interaction",
        }
    ]
    events = groups_to_events(groups, start_sec=60, end_sec=90, coverage_pct=80)
    assert len(events) == 1
    assert events[0]["kind"] == "interaction"
    assert events[0]["group_label"] == "Group A"
    assert "R2C3" in events[0]["seat_ids"]
