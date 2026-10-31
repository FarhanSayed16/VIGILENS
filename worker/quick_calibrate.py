"""
Quick classroom calibration presets.

Lecturer picks where the camera sits relative to the class; we propose
normalized seat boxes + a teaching-target ROI. Facing vector for TTOI is
still derived as seat-cluster → target centroid (regions.teaching_target_geometry).

Placements (image coords: x right, y down):
  back_of_room  — camera behind students, looking toward board
  facing_class  — camera near board / front, looking at student faces
  left_side     — camera on left wall, looking across rows
  right_side    — camera on right wall, looking across rows
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

Placement = Literal["back_of_room", "facing_class", "left_side", "right_side"]

PLACEMENTS: Tuple[Placement, ...] = (
    "back_of_room",
    "facing_class",
    "left_side",
    "right_side",
)


def _box(
    sid: str, x: float, y: float, w: float, h: float, label: Optional[str] = None
) -> Dict[str, Any]:
    return {
        "type": "box",
        "id": sid,
        "label": label or sid,
        "x": round(max(0.0, min(1.0, x)), 4),
        "y": round(max(0.0, min(1.0, y)), 4),
        "w": round(max(0.02, min(1.0 - x, w)), 4),
        "h": round(max(0.02, min(1.0 - y, h)), 4),
    }


def _seat_band(placement: Placement) -> Tuple[float, float, float, float]:
    """Return (x, y, w, h) of the student area in normalized coords."""
    if placement == "back_of_room":
        # Students fill lower/mid frame; board usually near top
        return 0.05, 0.28, 0.90, 0.68
    if placement == "facing_class":
        # Faces fill most of frame; board often behind camera → virtual target at top
        return 0.08, 0.18, 0.84, 0.72
    if placement == "left_side":
        # Looking right across class; students on rightish half
        return 0.28, 0.18, 0.68, 0.72
    # right_side
    return 0.04, 0.18, 0.68, 0.72


def _target_for(placement: Placement) -> Optional[Dict[str, Any]]:
    """
    Suggested teaching-target ROI, or None when board is not in frame.

    facing_class → no board box (students look at camera = toward board).
    """
    if placement == "facing_class":
        return None
    if placement == "back_of_room":
        return _box("teaching_target", 0.25, 0.02, 0.50, 0.18, "Board / screen")
    if placement == "left_side":
        return _box("teaching_target", 0.02, 0.10, 0.22, 0.55, "Board / screen")
    return _box("teaching_target", 0.76, 0.10, 0.22, 0.55, "Board / screen")


def facing_mode_for(placement: Placement) -> str:
    """toward_camera when board is behind the lens; else toward_board in-frame."""
    if placement == "facing_class":
        return "toward_camera"
    return "toward_board"


def suggest_seat_grid(
    placement: Placement,
    *,
    rows: int = 3,
    cols: int = 4,
    gap: float = 0.02,
) -> List[Dict[str, Any]]:
    """Fill the student band with a rows×cols grid of seat boxes."""
    rows = max(1, min(12, int(rows)))
    cols = max(1, min(12, int(cols)))
    bx, by, bw, bh = _seat_band(placement)
    gap_x = gap
    gap_y = gap
    cell_w = (bw - gap_x * (cols - 1)) / cols
    cell_h = (bh - gap_y * (rows - 1)) / rows
    seats: List[Dict[str, Any]] = []
    n = 0
    for r in range(rows):
        for c in range(cols):
            n += 1
            x = bx + c * (cell_w + gap_x)
            y = by + r * (cell_h + gap_y)
            seats.append(_box(f"s{n}", x, y, cell_w, cell_h, f"Seat {n}"))
    return seats


def suggest_layout(
    placement: str,
    *,
    rows: int = 3,
    cols: int = 4,
) -> Dict[str, Any]:
    if placement not in PLACEMENTS:
        raise ValueError(
            f"Unknown placement {placement!r}; choose one of {', '.join(PLACEMENTS)}"
        )
    p: Placement = placement  # type: ignore[assignment]
    target = _target_for(p)
    mode = facing_mode_for(p)
    return {
        "placement": p,
        "seat_regions": [],
        "target_roi": target,
        "facing_mode": mode,
        "hint": _hint(p),
    }


def _hint(placement: Placement) -> str:
    return {
        "back_of_room": (
            "Camera behind the class. Seats are registered from faces when the "
            "lecture starts. The amber box is only the board direction."
        ),
        "facing_class": (
            "Camera facing students. No seat boxes to draw. Looking at the camera "
            "counts as facing the front once a face locks."
        ),
        "left_side": (
            "Camera on the left wall. Faces register their own seats at Start. "
            "The amber box marks the board direction."
        ),
        "right_side": (
            "Camera on the right wall. Faces register their own seats at Start. "
            "The amber box marks the board direction."
        ),
    }[placement]


def target_from_click(
    x_norm: float, y_norm: float, *, w: float = 0.36, h: float = 0.16
) -> Dict[str, Any]:
    """Place a teaching-target box centered on a lecturer click."""
    x = max(0.0, min(1.0 - w, float(x_norm) - w / 2))
    y = max(0.0, min(1.0 - h, float(y_norm) - h / 2))
    return _box("teaching_target", x, y, w, h, "Board / screen")


def seats_from_person_boxes(
    boxes_norm: List[Tuple[float, float, float, float]],
    *,
    pad: float = 0.04,
) -> List[Dict[str, Any]]:
    """
    Convert person detections (x1,y1,x2,y2 normalized) into seat boxes.
    Pads slightly so fidgeting still maps to the same seat.
    Sorted top→bottom, left→right for stable seat ids.
    """
    ordered = sorted(
        boxes_norm,
        key=lambda b: ((b[1] + b[3]) / 2.0, (b[0] + b[2]) / 2.0),
    )
    seats: List[Dict[str, Any]] = []
    for i, (x1, y1, x2, y2) in enumerate(ordered, start=1):
        x1, y1 = max(0.0, x1 - pad), max(0.0, y1 - pad)
        x2, y2 = min(1.0, x2 + pad), min(1.0, y2 + pad)
        seats.append(
            _box(f"s{i}", x1, y1, max(0.04, x2 - x1), max(0.06, y2 - y1), f"Seat {i}")
        )
    return seats


def detect_people_seats(
    image_bgr,
    *,
    weights: Optional[str] = None,
    conf: float = 0.25,
) -> List[Dict[str, Any]]:
    """Run YOLOv8-pose person boxes → seat regions. Raises on missing deps."""
    from worker import config, vision_yolo

    if image_bgr is None or getattr(image_bgr, "size", 0) == 0:
        raise ValueError("Empty calibration image")
    h, w = image_bgr.shape[:2]
    if h < 1 or w < 1:
        raise ValueError("Invalid calibration image size")
    weights_raw = weights or (config.load_config().get("models") or {}).get(
        "yolo_pose_weights", "yolov8n-pose.pt"
    )
    path = config.resolve_model_path(weights_raw)
    if not path.is_file():
        path = config.REPO_ROOT / "models" / path.name
        path.parent.mkdir(parents=True, exist_ok=True)
    model = vision_yolo.load_yolo_pose(str(path))
    people = vision_yolo.detect_persons(model, image_bgr, conf=conf)
    boxes: List[Tuple[float, float, float, float]] = []
    for p in people:
        x1, y1, x2, y2 = p.bbox_xyxy
        boxes.append((x1 / w, y1 / h, x2 / w, y2 / h))
    return seats_from_person_boxes(boxes)


def facing_sanity(placement: Placement) -> Dict[str, float]:
    """
    Expected facing-vector signs for unit tests / docs.
    toward_camera → (0, -1); else seat-cluster → target.
    """
    from worker import regions

    layout = suggest_layout(placement, rows=2, cols=2)
    if layout["facing_mode"] == "toward_camera":
        return {"fx": 0.0, "fy": -1.0}
    target = regions.parse_target(layout["target_roi"])
    assert target is not None
    tc = target.centroid_norm()
    fx, fy = float(tc[0] - 0.5), float(tc[1] - 0.5)
    norm = max(1e-6, (fx * fx + fy * fy) ** 0.5)
    return {"fx": fx / norm, "fy": fy / norm}
