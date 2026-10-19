"""Quick calibration presets produce valid seats + sensible facing vectors."""

from worker import quick_calibrate, regions


def test_all_placements_have_seats_and_target():
    for p in quick_calibrate.PLACEMENTS:
        layout = quick_calibrate.suggest_layout(p, rows=2, cols=3)
        assert len(layout["seat_regions"]) == 6
        if p == "facing_class":
            assert layout["target_roi"] is None
            assert layout["facing_mode"] == "toward_camera"
        else:
            t = layout["target_roi"]
            assert t["id"] == "teaching_target"
            assert 0 <= t["x"] < 1 and t["w"] > 0
            assert layout["facing_mode"] == "toward_board"
        for s in layout["seat_regions"]:
            assert s["x"] + s["w"] <= 1.0001
            assert s["y"] + s["h"] <= 1.0001


def test_target_from_click_centered():
    t = quick_calibrate.target_from_click(0.5, 0.5, w=0.2, h=0.1)
    assert abs(t["x"] + t["w"] / 2 - 0.5) < 1e-3
    assert abs(t["y"] + t["h"] / 2 - 0.5) < 1e-3


def test_side_targets_differ():
    left = quick_calibrate.suggest_layout("left_side")["target_roi"]
    right = quick_calibrate.suggest_layout("right_side")["target_roi"]
    assert left["x"] < right["x"]


def test_facing_back_of_room_points_up():
    f = quick_calibrate.facing_sanity("back_of_room")
    assert f["fy"] < -0.3


def test_facing_class_toward_camera():
    f = quick_calibrate.facing_sanity("facing_class")
    assert f["fy"] == -1.0
    assert f["fx"] == 0.0


def test_facing_left_side_points_left():
    f = quick_calibrate.facing_sanity("left_side")
    assert f["fx"] < -0.3


def test_facing_right_side_points_right():
    f = quick_calibrate.facing_sanity("right_side")
    assert f["fx"] > 0.3


def test_yaw_prime_zero_when_facing_camera_facing_class():
    rel = regions.yaw_relative_to_target_deg(
        0.0, facing_vector_norm=(0.0, -1.0)
    )
    assert abs(rel) < 25.0


def test_seats_from_boxes_sorted():
    boxes = [(0.5, 0.5, 0.7, 0.9), (0.1, 0.2, 0.3, 0.5)]
    seats = quick_calibrate.seats_from_person_boxes(boxes, pad=0)
    assert seats[0]["id"] == "s1"
    assert seats[0]["x"] < seats[1]["x"] or seats[0]["y"] < seats[1]["y"]
