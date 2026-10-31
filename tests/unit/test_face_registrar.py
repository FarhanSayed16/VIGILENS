"""A seat exists only after a face with both eyes holds still."""

from worker.face_registrar import FaceSeatRegistrar, FaceSighting


def _face(x1, y1, x2, y2, t, eyes=True, yaw=0.0):
    return FaceSighting(
        bbox_xyxy=(float(x1), float(y1), float(x2), float(y2)),
        eyes_visible=eyes,
        time_sec=t,
        yaw_deg=yaw,
        pitch_deg=0.0,
        face_width_px=float(x2 - x1),
    )


def _hold(reg, box, steps, yaw=0.0):
    x1, y1, x2, y2 = box
    last = []
    for i in range(steps):
        t = i * 0.5
        last = reg.update(
            [_face(x1, y1, x2, y2, t, yaw=yaw)],
            time_sec=t,
            frame_width=640,
            frame_height=480,
        )
    return last


def test_moving_camera_does_not_lock():
    reg = FaceSeatRegistrar()
    boxes = []
    for i in range(8):
        t = i * 0.4
        # Jump farther than the stillness threshold (camera being waved).
        shift = i * 80
        boxes = reg.update(
            [_face(40 + shift, 40, 140 + shift, 180, t)],
            time_sec=t,
            frame_width=640,
            frame_height=480,
        )
    assert reg.locked_ids() == []
    assert boxes
    assert boxes[0].locked is False
    assert "still" in reg.hint(3.0).lower()


def test_steady_face_with_eyes_locks_p1():
    reg = FaceSeatRegistrar()
    boxes = _hold(reg, (100, 80, 220, 240), steps=6)
    assert reg.locked_ids() == ["P1"]
    assert boxes[0].slot_id == "P1"
    assert boxes[0].locked is True
    feats = reg.to_features(2.5)
    assert len(feats) == 1
    assert feats[0].seat_id == "P1"
    assert feats[0].occupied is True


def test_second_steady_face_locks_p2():
    reg = FaceSeatRegistrar()
    for i in range(6):
        t = i * 0.5
        reg.update(
            [
                _face(40, 60, 150, 220, t),
                _face(400, 70, 520, 230, t),
            ],
            time_sec=t,
            frame_width=640,
            frame_height=480,
        )
    assert sorted(reg.locked_ids()) == ["P1", "P2"]


def test_no_face_means_zero_seats():
    reg = FaceSeatRegistrar()
    boxes = reg.update([], time_sec=1.0, frame_width=640, frame_height=480)
    assert boxes == []
    assert reg.locked_ids() == []
    assert reg.to_features(1.0) == []


def test_body_without_eyes_is_not_a_seat():
    reg = FaceSeatRegistrar()
    for i in range(6):
        t = i * 0.5
        reg.update(
            [_face(100, 80, 220, 240, t, eyes=False)],
            time_sec=t,
            frame_width=640,
            frame_height=480,
        )
    assert reg.locked_ids() == []
