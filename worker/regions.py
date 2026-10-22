"""
Seat / teaching-target geometry helpers.

Regions use normalized [0,1] coordinates (same as room_configs JSON).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

Point = Tuple[float, float]


@dataclass
class SeatRegion:
    id: str
    label: Optional[str]
    kind: str  # box | polygon
    # Polygon in normalized coords (closed implicitly)
    polygon_norm: np.ndarray  # shape (N, 2)

    def centroid_norm(self) -> Point:
        pts = self.polygon_norm
        return float(pts[:, 0].mean()), float(pts[:, 1].mean())

    def contains_norm(self, x: float, y: float) -> bool:
        """Point-in-polygon (normalized space) via OpenCV when available."""
        try:
            import cv2

            contour = (self.polygon_norm * 1000.0).astype(np.float32)
            # scale for numeric stability; use same scale for point
            return (
                cv2.pointPolygonTest(contour, (x * 1000.0, y * 1000.0), False) >= 0
            )
        except Exception:
            # Axis-aligned bbox fallback
            xs, ys = self.polygon_norm[:, 0], self.polygon_norm[:, 1]
            return float(xs.min()) <= x <= float(xs.max()) and float(ys.min()) <= y <= float(
                ys.max()
            )


@dataclass
class TargetGeometry:
    id: str
    polygon_norm: np.ndarray
    centroid_norm: Point
    # Unit vector in image plane from seat-area center toward target (for yaw baseline)
    facing_vector_norm: Point


def _box_to_poly(x: float, y: float, w: float, h: float) -> np.ndarray:
    return np.array(
        [[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
        dtype=np.float64,
    )


def parse_region(raw: Dict[str, Any]) -> SeatRegion:
    kind = raw.get("type") or "box"
    rid = str(raw.get("id") or "region")
    label = raw.get("label")
    if kind == "polygon":
        pts = np.array(raw["points"], dtype=np.float64)
        if pts.ndim != 2 or pts.shape[1] != 2 or pts.shape[0] < 3:
            raise ValueError(f"Invalid polygon for region {rid}")
        return SeatRegion(id=rid, label=label, kind="polygon", polygon_norm=pts)
    # box
    poly = _box_to_poly(
        float(raw["x"]), float(raw["y"]), float(raw["w"]), float(raw["h"])
    )
    return SeatRegion(id=rid, label=label, kind="box", polygon_norm=poly)


def parse_seat_regions(raw_list: Optional[Sequence[Dict[str, Any]]]) -> List[SeatRegion]:
    if not raw_list:
        return []
    return [parse_region(r) for r in raw_list]


def parse_target(raw: Optional[Dict[str, Any]]) -> Optional[SeatRegion]:
    if not raw:
        return None
    return parse_region(raw)


def pixel_to_norm(x_px: float, y_px: float, width: int, height: int) -> Point:
    if width <= 0 or height <= 0:
        raise ValueError("Frame size must be positive")
    return x_px / width, y_px / height


def norm_to_pixel(x: float, y: float, width: int, height: int) -> Tuple[int, int]:
    return int(round(x * width)), int(round(y * height))


def assign_point_to_seat(
    x_norm: float,
    y_norm: float,
    seats: Sequence[SeatRegion],
) -> Optional[str]:
    """Return seat id containing the point, or None."""
    for seat in seats:
        if seat.contains_norm(x_norm, y_norm):
            return seat.id
    return None


def assign_detection_to_seats(
    detections_norm: Iterable[Point],
    seats: Sequence[SeatRegion],
) -> Dict[str, List[int]]:
    """
    Map detection indices into seat ids.
    detections_norm: iterable of (x, y) in normalized coords (e.g. person ankle/hip).
    """
    out: Dict[str, List[int]] = {s.id: [] for s in seats}
    for i, (x, y) in enumerate(detections_norm):
        sid = assign_point_to_seat(x, y, seats)
        if sid is not None:
            out[sid].append(i)
    return out


def teaching_target_geometry(
    target: SeatRegion,
    seats: Sequence[SeatRegion],
) -> TargetGeometry:
    """
    Target centroid + facing vector from classroom seat cluster toward target.

    Facing vector is in normalized image coords (x right, y down).
    Yaw baseline helpers use this as "toward board" direction.
    """
    tc = target.centroid_norm()
    if seats:
        sc = np.array([s.centroid_norm() for s in seats], dtype=np.float64).mean(axis=0)
        fx, fy = float(tc[0] - sc[0]), float(tc[1] - sc[1])
    else:
        # Default: face upward in image (toward typical board at top)
        fx, fy = 0.0, -1.0
    norm = (fx * fx + fy * fy) ** 0.5
    if norm < 1e-6:
        fx, fy = 0.0, -1.0
        norm = 1.0
    fx, fy = fx / norm, fy / norm
    return TargetGeometry(
        id=target.id,
        polygon_norm=target.polygon_norm,
        centroid_norm=tc,
        facing_vector_norm=(fx, fy),
    )


def yaw_relative_to_target_deg(
    person_yaw_deg: float,
    *,
    facing_vector_norm: Point,
    camera_yaw_zero_is_optical_axis: bool = True,
) -> float:
    """
    Convert absolute head yaw (MediaPipe/solvePnP style, degrees) into
    yaw' relative to teaching-target facing.

    Convention (MVP):
    - person_yaw_deg: 0 looking along camera optical axis, + right
    - facing_vector_norm: direction from seats toward target in image plane
    - We map facing vector to an approximate yaw offset via atan2(fx, -fy)
      (image y down → "up the frame" is negative y).
    """
    fx, fy = facing_vector_norm
    # Angle of facing in image plane; 0 ≈ looking toward top of frame
    target_yaw = float(np.degrees(np.arctan2(fx, -fy)))
    if camera_yaw_zero_is_optical_axis:
        # Optical axis ≈ looking into scene; treat as yaw 0 baseline
        rel = person_yaw_deg - target_yaw
    else:
        rel = person_yaw_deg - target_yaw
    # Wrap to [-180, 180]
    while rel > 180:
        rel -= 360
    while rel < -180:
        rel += 360
    return rel


def is_target_oriented(
    yaw_prime_deg: float,
    *,
    yaw_threshold_deg: float = 30.0,
) -> bool:
    """True if |yaw'| is within the teaching-target orientation band."""
    return abs(yaw_prime_deg) <= yaw_threshold_deg
