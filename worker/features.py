"""
Per-seat / per-window feature extraction.

Phase 17: Tier-1 occupancy + shoulder proxy from YOLO pose.
Phase 18: Tier-2 MediaPipe head pose when face large enough; else Tier-1; else unobservable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Tuple

import numpy as np

from worker.regions import (
    Point,
    is_target_oriented,
    yaw_relative_to_target_deg,
)
from worker.seat_mapping import FrameSeatMap
from worker.vision_mediapipe import HeadPoseResult, estimate_head_pose
from worker.vision_yolo import PersonDetection


# Observable-state labels used by aggregation / product copy
STATE_TARGET_ORIENTED = "target_oriented"
STATE_NOT_TARGET_ORIENTED = "not_target_oriented"
STATE_HEAD_DOWN_CUE = "head_down_cue"
STATE_HAND_RAISED = "hand_raised"
STATE_UNOBSERVABLE = "unobservable"
STATE_EMPTY = "empty"


@dataclass
class SeatFrameFeature:
    seat_id: str
    time_sec: float
    occupied: bool
    target_oriented: Optional[bool] = None
    yaw_prime_deg: Optional[float] = None
    pitch_deg: Optional[float] = None
    head_down_cue: bool = False
    hand_raised: bool = False
    tier: Optional[int] = None  # 1 body, 2 head; None = unobservable / empty
    data_quality_note: Optional[str] = None
    person_conf: Optional[float] = None
    face_width_px: Optional[float] = None

    def is_observable(self) -> bool:
        return self.occupied and self.tier is not None and self.yaw_prime_deg is not None

    def observation_state(self, *, teaching_mode: Optional[str] = None) -> str:
        """
        Primary label for this sample.
        Mode hook: note_taking treats head-down as non-failure when yaw is OK.
        """
        if not self.occupied or self.data_quality_note == "empty":
            return STATE_EMPTY
        if not self.is_observable():
            return STATE_UNOBSERVABLE
        if self.hand_raised:
            return STATE_HAND_RAISED
        aligned = sample_aligned(
            self,
            teaching_mode=teaching_mode,
            yaw_threshold_deg=30.0,
            tier1_yaw_threshold_deg=45.0,
        )
        if aligned and self.head_down_cue and _mode_allows_head_down(teaching_mode):
            return STATE_HEAD_DOWN_CUE  # still counts as oriented for scoring
        if aligned:
            return STATE_TARGET_ORIENTED
        if self.head_down_cue and not _mode_allows_head_down(teaching_mode):
            return STATE_HEAD_DOWN_CUE
        return STATE_NOT_TARGET_ORIENTED


def _mode_allows_head_down(teaching_mode: Optional[str]) -> bool:
    return (teaching_mode or "").lower() in {"note_taking", "note-taking"}


def sample_aligned(
    feat: SeatFrameFeature,
    *,
    teaching_mode: Optional[str] = None,
    yaw_threshold_deg: float = 30.0,
    tier1_yaw_threshold_deg: float = 45.0,
    respect_teaching_modes: bool = True,
) -> Optional[bool]:
    """
    Whether this sample counts as target-oriented for TTOI.

    Returns None if unobservable (exclude from ratio).
    note_taking: head-down does not fail the sample when yaw is within band.
    Tier-1 uses a wider yaw band (coarser body proxy).
    """
    if not feat.is_observable():
        return None
    thr = (
        tier1_yaw_threshold_deg if feat.tier == 1 else yaw_threshold_deg
    )
    yaw_ok = abs(float(feat.yaw_prime_deg)) <= thr
    if not yaw_ok:
        return False
    if feat.head_down_cue:
        if respect_teaching_modes and _mode_allows_head_down(teaching_mode):
            return True
        return False
    return True


def _person_face_crop(
    frame_bgr: np.ndarray,
    person: PersonDetection,
    *,
    top_fraction: float = 0.45,
    pad_frac: float = 0.08,
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Crop upper portion of person bbox (likely face).
    Returns (crop_bgr, (x0, y0) offset into full frame).
    """
    h, w = frame_bgr.shape[:2]
    x1, y1, x2, y2 = person.bbox_xyxy
    bw = max(1.0, x2 - x1)
    bh = max(1.0, y2 - y1)
    pad_x = bw * pad_frac
    pad_y = bh * pad_frac
    cx1 = max(0, int(x1 - pad_x))
    cy1 = max(0, int(y1 - pad_y))
    cx2 = min(w, int(x2 + pad_x))
    # Prefer upper band of the person box
    cy2 = min(h, int(y1 + bh * top_fraction + pad_y))
    if cy2 <= cy1 + 4 or cx2 <= cx1 + 4:
        return frame_bgr, (0, 0)
    return frame_bgr[cy1:cy2, cx1:cx2].copy(), (cx1, cy1)


def _tier1_from_person(
    seat_id: str,
    time_sec: float,
    person: PersonDetection,
    *,
    tier1_yaw_threshold_deg: float = 45.0,
) -> SeatFrameFeature:
    shoulder = person.torso_yaw_proxy_deg()
    oriented = (
        abs(shoulder) <= tier1_yaw_threshold_deg if shoulder is not None else None
    )
    note = None
    if shoulder is None:
        note = "unobservable"
    return SeatFrameFeature(
        seat_id=seat_id,
        time_sec=time_sec,
        occupied=True,
        target_oriented=oriented,
        yaw_prime_deg=shoulder,
        hand_raised=person.hand_raised(),
        tier=1 if shoulder is not None else None,
        data_quality_note=note,
        person_conf=person.conf,
    )


def fuse_seat_feature(
    seat_id: str,
    time_sec: float,
    person: Optional[PersonDetection],
    *,
    frame_bgr: Optional[np.ndarray] = None,
    landmarker: Any = None,
    face_width_min_px: float = 80.0,
    pitch_down_threshold_deg: float = 20.0,
    enable_tier2: bool = True,
    facing_vector_norm: Optional[Point] = None,
    yaw_threshold_deg: float = 30.0,
    tier1_yaw_threshold_deg: float = 45.0,
) -> SeatFrameFeature:
    """
    Pick Tier-2 (head) when face large enough, else Tier-1 (body), else unobservable.
    """
    if person is None:
        return SeatFrameFeature(
            seat_id=seat_id,
            time_sec=time_sec,
            occupied=False,
            tier=None,
            data_quality_note="empty",
        )

    head: Optional[HeadPoseResult] = None
    if (
        enable_tier2
        and landmarker is not None
        and frame_bgr is not None
        and frame_bgr.size > 0
    ):
        crop, _offset = _person_face_crop(frame_bgr, person)
        # Person-bbox crop only — no full-frame fallback (avoids wrong-face→seat)
        if crop is not frame_bgr and crop.size > 0:
            head = estimate_head_pose(
                landmarker,
                crop,
                face_width_min_px=face_width_min_px,
                face_index=0,
            )

    if head is not None:
        yaw_abs = head.yaw_deg
        if facing_vector_norm is not None:
            yaw_prime = yaw_relative_to_target_deg(
                yaw_abs, facing_vector_norm=facing_vector_norm
            )
        else:
            yaw_prime = yaw_abs
        oriented = is_target_oriented(yaw_prime, yaw_threshold_deg=yaw_threshold_deg)
        head_down = head.pitch_deg >= pitch_down_threshold_deg
        return SeatFrameFeature(
            seat_id=seat_id,
            time_sec=time_sec,
            occupied=True,
            target_oriented=oriented,
            yaw_prime_deg=yaw_prime,
            pitch_deg=head.pitch_deg,
            head_down_cue=head_down,
            hand_raised=person.hand_raised(),
            tier=2,
            person_conf=person.conf,
            face_width_px=head.face_width_px,
        )

    # Tier-1 body fallback — map shoulder proxy into target-relative yaw' when possible
    feat = _tier1_from_person(
        seat_id,
        time_sec,
        person,
        tier1_yaw_threshold_deg=tier1_yaw_threshold_deg,
    )
    if feat.yaw_prime_deg is not None and facing_vector_norm is not None:
        feat.yaw_prime_deg = yaw_relative_to_target_deg(
            float(feat.yaw_prime_deg),
            facing_vector_norm=facing_vector_norm,
        )
        feat.target_oriented = abs(float(feat.yaw_prime_deg)) <= tier1_yaw_threshold_deg
    if feat.tier is None:
        feat.data_quality_note = "unobservable"
    elif enable_tier2:
        feat.data_quality_note = feat.data_quality_note or "tier1_face_small"
    return feat


def tier1_features_from_frame_map(
    frame_map: FrameSeatMap,
    *,
    tier1_yaw_threshold_deg: float = 45.0,
) -> List[SeatFrameFeature]:
    """Build per-seat features for one frame from YOLO seat assignments (Tier-1 only)."""
    out: List[SeatFrameFeature] = []
    for sid, idxs in frame_map.seat_to_person_indices.items():
        if not idxs:
            out.append(
                SeatFrameFeature(
                    seat_id=sid,
                    time_sec=frame_map.time_sec,
                    occupied=False,
                    tier=None,
                    data_quality_note="empty",
                )
            )
            continue
        best_i = max(idxs, key=lambda i: frame_map.persons[i].conf)
        person = frame_map.persons[best_i]
        out.append(
            _tier1_from_person(
                sid,
                frame_map.time_sec,
                person,
                tier1_yaw_threshold_deg=tier1_yaw_threshold_deg,
            )
        )
    return out


def features_from_frame_map(
    frame_map: FrameSeatMap,
    *,
    frame_bgr: Optional[np.ndarray] = None,
    landmarker: Any = None,
    face_width_min_px: float = 80.0,
    pitch_down_threshold_deg: float = 20.0,
    enable_tier2: bool = True,
    facing_vector_norm: Optional[Point] = None,
    yaw_threshold_deg: float = 30.0,
    tier1_yaw_threshold_deg: float = 45.0,
) -> List[SeatFrameFeature]:
    """Per-seat fused Tier-1 / Tier-2 features for one frame."""
    out: List[SeatFrameFeature] = []
    for sid, idxs in frame_map.seat_to_person_indices.items():
        person = None
        if idxs:
            best_i = max(idxs, key=lambda i: frame_map.persons[i].conf)
            person = frame_map.persons[best_i]
        out.append(
            fuse_seat_feature(
                sid,
                frame_map.time_sec,
                person,
                frame_bgr=frame_bgr,
                landmarker=landmarker,
                face_width_min_px=face_width_min_px,
                pitch_down_threshold_deg=pitch_down_threshold_deg,
                enable_tier2=enable_tier2,
                facing_vector_norm=facing_vector_norm,
                yaw_threshold_deg=yaw_threshold_deg,
                tier1_yaw_threshold_deg=tier1_yaw_threshold_deg,
            )
        )
    return out


def extract_seat_features(
    frame_maps: Sequence[FrameSeatMap],
) -> List[List[SeatFrameFeature]]:
    """Per-frame list of seat features (Tier-1)."""
    return [tier1_features_from_frame_map(fm) for fm in frame_maps]
