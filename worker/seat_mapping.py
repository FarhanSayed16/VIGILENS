"""
Assign YOLO persons to seat regions + occupied-seat calibration.

Supports classroom dynamics: soft nearest-seat assign, one person per drawn
seat, and ephemeral virtual seats for extra people in view (arrive/leave).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from worker.regions import SeatRegion, assign_point_to_seat, pixel_to_norm
from worker.vision_yolo import PersonDetection


@dataclass
class FrameSeatMap:
    """Per-frame assignment of person indices → seat ids."""

    time_sec: float
    persons: List[PersonDetection]
    seat_to_person_indices: Dict[str, List[int]] = field(default_factory=dict)
    unassigned_indices: List[int] = field(default_factory=list)


@dataclass
class OccupancyCalibration:
    """
    Calibration over a short window of frames.

    A seat is occupied if it had a person in >= occupied_seat_min_fraction of samples.
    n_expected = count of occupied seats (proxy for class size in view).
    """

    n_frames: int
    seat_occupancy_fraction: Dict[str, float]
    occupied_seat_ids: List[str]
    n_expected: int
    occupied_seat_min_fraction: float


def _bbox_iou(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    denom = area_a + area_b - inter
    return float(inter / denom) if denom > 1e-6 else 0.0


def dedupe_persons(
    persons: Sequence[PersonDetection],
    *,
    iou_thresh: float = 0.55,
) -> List[PersonDetection]:
    """Drop overlapping duplicate detections (keep higher confidence)."""
    ordered = sorted(persons, key=lambda p: float(p.conf), reverse=True)
    kept: List[PersonDetection] = []
    for p in ordered:
        if any(_bbox_iou(p.bbox_xyxy, k.bbox_xyxy) >= iou_thresh for k in kept):
            continue
        kept.append(p)
    return kept


def _nearest_seat(
    xn: float,
    yn: float,
    seats: Sequence[SeatRegion],
) -> Tuple[Optional[str], float]:
    best_id: Optional[str] = None
    best_d = 1e9
    for s in seats:
        cx, cy = s.centroid_norm()
        d = math.hypot(xn - float(cx), yn - float(cy))
        if d < best_d:
            best_d = d
            best_id = s.id
    return best_id, best_d


def assign_persons_to_seats(
    persons: Sequence[PersonDetection],
    seats: Sequence[SeatRegion],
    *,
    frame_width: int,
    frame_height: int,
    time_sec: float = 0.0,
    soft_radius_norm: float = 0.18,
    virtual_for_unassigned: bool = True,
    max_virtual_seats: int = 60,
) -> FrameSeatMap:
    """
    Map each person to at most one seat via hip/bbox anchor.

    - Polygon / box hit first
    - Then soft nearest seat within ``soft_radius_norm``
    - Contested seats keep the highest-confidence person
    - Remaining people get ephemeral ``v1…vN`` seats so classmates who enter
      or leave the frame still contribute to live orientation metrics
    """
    people = dedupe_persons(persons)
    for p in people:
        p.seat_id = None

    seat_ids = [s.id for s in seats]
    seat_to: Dict[str, List[int]] = {sid: [] for sid in seat_ids}
    tentative: Dict[int, Optional[str]] = {}

    for i, p in enumerate(people):
        ax, ay = p.anchor_xy()
        xn, yn = pixel_to_norm(ax, ay, frame_width, frame_height)
        sid = assign_point_to_seat(xn, yn, seats)
        if sid is None:
            near_id, dist = _nearest_seat(xn, yn, seats)
            if near_id is not None and dist <= soft_radius_norm:
                sid = near_id
        tentative[i] = sid

    claimed: Dict[str, int] = {}
    for i, sid in tentative.items():
        if sid is None:
            continue
        prev = claimed.get(sid)
        if prev is None or float(people[i].conf) > float(people[prev].conf):
            claimed[sid] = i

    # Solo / desk: one seat + everyone outside → claim strongest into that seat
    if len(seats) == 1 and seats[0].id not in claimed:
        only = seats[0].id
        if people:
            best_i = max(range(len(people)), key=lambda i: float(people[i].conf))
            claimed[only] = best_i

    winners = set(claimed.values())
    for sid, idx in claimed.items():
        seat_to[sid] = [idx]
        people[idx].seat_id = sid

    unassigned = [i for i in range(len(people)) if i not in winners]

    # Ephemeral seats for extras (sorted left→right for stable in-frame labels)
    if virtual_for_unassigned and unassigned:
        ordered = sorted(
            unassigned,
            key=lambda i: people[i].anchor_xy()[0],
        )[: max(0, int(max_virtual_seats))]
        for n, idx in enumerate(ordered, start=1):
            vid = f"v{n}"
            seat_to[vid] = [idx]
            people[idx].seat_id = vid
        unassigned = [i for i in unassigned if people[i].seat_id is None]

    return FrameSeatMap(
        time_sec=time_sec,
        persons=list(people),
        seat_to_person_indices=seat_to,
        unassigned_indices=unassigned,
    )


def calibrate_occupancy(
    frame_maps: Sequence[FrameSeatMap],
    seats: Sequence[SeatRegion],
    *,
    occupied_seat_min_fraction: float = 0.5,
) -> OccupancyCalibration:
    """
    Compute per-seat occupancy fraction across calibration frames.
    """
    if not frame_maps:
        return OccupancyCalibration(
            n_frames=0,
            seat_occupancy_fraction={s.id: 0.0 for s in seats},
            occupied_seat_ids=[],
            n_expected=0,
            occupied_seat_min_fraction=occupied_seat_min_fraction,
        )

    n = len(frame_maps)
    hits = {s.id: 0 for s in seats}
    for fm in frame_maps:
        for sid, idxs in fm.seat_to_person_indices.items():
            if sid in hits and idxs:
                hits[sid] = hits.get(sid, 0) + 1

    fracs = {sid: hits.get(sid, 0) / n for sid in hits}
    occupied = [
        sid
        for sid, f in fracs.items()
        if f >= occupied_seat_min_fraction
    ]
    # Also count virtual seats that appeared in most recent maps
    virtual_hits: Dict[str, int] = {}
    for fm in frame_maps:
        for sid, idxs in fm.seat_to_person_indices.items():
            if sid.startswith("v") and idxs:
                virtual_hits[sid] = virtual_hits.get(sid, 0) + 1
    for sid, h in virtual_hits.items():
        if h / n >= occupied_seat_min_fraction:
            occupied.append(sid)

    return OccupancyCalibration(
        n_frames=n,
        seat_occupancy_fraction=fracs,
        occupied_seat_ids=occupied,
        n_expected=len(occupied),
        occupied_seat_min_fraction=occupied_seat_min_fraction,
    )
