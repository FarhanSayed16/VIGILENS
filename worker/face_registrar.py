"""
Session-only face seats.

A slot is created only when a face with both eyes stays still.
No drawn chairs, no empty placeholders, no identity across lectures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from worker.features import SeatFrameFeature
from worker.regions import is_target_oriented, yaw_relative_to_target_deg

BBox = Tuple[float, float, float, float]


def _iou(a: BBox, b: BBox) -> float:
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


def _center(box: BBox) -> Tuple[float, float]:
    return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0


@dataclass
class FaceSighting:
    """One face in a frame. Tests build these directly; live fills them from landmarks."""

    bbox_xyxy: BBox
    eyes_visible: bool
    time_sec: float
    yaw_deg: Optional[float] = None
    pitch_deg: Optional[float] = None
    face_width_px: float = 0.0


@dataclass
class LiveFaceBox:
    bbox_xyxy: BBox
    slot_id: Optional[str]
    locked: bool
    moving: bool
    eyes_visible: bool


@dataclass
class _Track:
    bbox: BBox
    last_time: float
    stable_sec: float = 0.0
    slot_id: Optional[str] = None
    seen: bool = False
    moving: bool = False
    eyes_visible: bool = False
    yaw_deg: Optional[float] = None
    pitch_deg: Optional[float] = None
    face_width_px: float = 0.0


@dataclass
class FaceSeatRegistrar:
    """Lock P1, P2, … from stable faces. Never emits a seat that was not a face."""

    register_window_sec: float = 15.0
    stable_sec: float = 2.0
    lock_iou: float = 0.55
    # Center shift vs frame diagonal. Above this, the camera or the person is moving.
    move_frac: float = 0.035
    match_iou: float = 0.25
    _tracks: List[_Track] = field(default_factory=list)
    _next_slot: int = 1

    def locked_ids(self) -> List[str]:
        return [t.slot_id for t in self._tracks if t.slot_id]

    def hint(self, time_sec: float) -> str:
        n = len(self.locked_ids())
        moving = any(t.moving and t.seen for t in self._tracks)
        if moving and n == 0:
            return "Hold the camera still — a face box locks only when it stops moving."
        if time_sec <= self.register_window_sec and n == 0:
            return "Registering faces… hold the camera still. A seat appears only for a real face."
        if n == 0:
            return "No face registered yet. Look at the camera and hold still."
        if time_sec <= self.register_window_sec:
            return f"Registering faces… {n} locked. Hold steady for anyone still moving."
        return f"{n} people registered."

    def update(
        self,
        sightings: Sequence[FaceSighting],
        *,
        time_sec: float,
        frame_width: int,
        frame_height: int,
    ) -> List[LiveFaceBox]:
        diag = max(1.0, (frame_width**2 + frame_height**2) ** 0.5)
        for t in self._tracks:
            t.seen = False
            t.moving = False

        unused = list(range(len(self._tracks)))
        pairs: List[Tuple[float, int, int]] = []
        for si, sight in enumerate(sightings):
            if not sight.eyes_visible:
                continue
            for ti in unused:
                score = _iou(sight.bbox_xyxy, self._tracks[ti].bbox)
                if score >= self.match_iou:
                    pairs.append((score, si, ti))
        pairs.sort(reverse=True)
        taken_s: set[int] = set()
        taken_t: set[int] = set()
        for score, si, ti in pairs:
            if si in taken_s or ti in taken_t:
                continue
            taken_s.add(si)
            taken_t.add(ti)
            self._touch(self._tracks[ti], sightings[si], time_sec, diag, score)

        for si, sight in enumerate(sightings):
            if si in taken_s or not sight.eyes_visible:
                continue
            track = _Track(
                bbox=sight.bbox_xyxy,
                last_time=time_sec,
                seen=True,
                eyes_visible=True,
                yaw_deg=sight.yaw_deg,
                pitch_deg=sight.pitch_deg,
                face_width_px=sight.face_width_px,
            )
            self._tracks.append(track)

        boxes: List[LiveFaceBox] = []
        for t in self._tracks:
            if not t.seen:
                continue
            boxes.append(
                LiveFaceBox(
                    bbox_xyxy=t.bbox,
                    slot_id=t.slot_id,
                    locked=t.slot_id is not None,
                    moving=t.moving,
                    eyes_visible=t.eyes_visible,
                )
            )
        return boxes

    def _touch(
        self,
        track: _Track,
        sight: FaceSighting,
        time_sec: float,
        diag: float,
        iou: float,
    ) -> None:
        cx, cy = _center(sight.bbox_xyxy)
        px, py = _center(track.bbox)
        shift = ((cx - px) ** 2 + (cy - py) ** 2) ** 0.5 / diag
        dt = max(0.0, time_sec - track.last_time)
        still = iou >= self.lock_iou and shift <= self.move_frac
        track.moving = not still
        if still:
            track.stable_sec += dt
        else:
            track.stable_sec = 0.0
        track.bbox = sight.bbox_xyxy
        track.last_time = time_sec
        track.seen = True
        track.eyes_visible = True
        track.yaw_deg = sight.yaw_deg
        track.pitch_deg = sight.pitch_deg
        track.face_width_px = sight.face_width_px
        if track.slot_id is None and track.stable_sec >= self.stable_sec:
            track.slot_id = f"P{self._next_slot}"
            self._next_slot += 1

    def to_features(
        self,
        time_sec: float,
        *,
        facing_vector_norm: Tuple[float, float] = (0.0, -1.0),
        yaw_threshold_deg: float = 30.0,
        pitch_down_threshold_deg: float = 20.0,
    ) -> List[SeatFrameFeature]:
        """One sample per locked face. Unseen slots are unobservable, never empty chairs."""
        out: List[SeatFrameFeature] = []
        for t in self._tracks:
            if not t.slot_id:
                continue
            if not t.seen or t.yaw_deg is None:
                out.append(
                    SeatFrameFeature(
                        seat_id=t.slot_id,
                        time_sec=time_sec,
                        occupied=True,
                        tier=None,
                        data_quality_note="unobservable",
                    )
                )
                continue
            yaw_prime = yaw_relative_to_target_deg(
                float(t.yaw_deg),
                facing_vector_norm=facing_vector_norm,
            )
            oriented = is_target_oriented(yaw_prime, yaw_threshold_deg=yaw_threshold_deg)
            head_down = (
                t.pitch_deg is not None and t.pitch_deg >= pitch_down_threshold_deg
            )
            out.append(
                SeatFrameFeature(
                    seat_id=t.slot_id,
                    time_sec=time_sec,
                    occupied=True,
                    target_oriented=oriented,
                    yaw_prime_deg=yaw_prime,
                    pitch_deg=t.pitch_deg,
                    head_down_cue=head_down,
                    tier=2,
                    face_width_px=t.face_width_px or None,
                    person_conf=0.9,
                )
            )
        return out
