"""
YOLOv8-pose Tier-1 path — person boxes + COCO-17 keypoints.

Weights auto-download on first load (ultralytics).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# COCO-17 keypoint names (Ultralytics pose order)
KEYPOINT_NAMES = (
    "nose",
    "left_eye",
    "right_eye",
    "left_ear",
    "right_ear",
    "left_shoulder",
    "right_shoulder",
    "left_elbow",
    "right_elbow",
    "left_wrist",
    "right_wrist",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
)

KP_LEFT_HIP = 11
KP_RIGHT_HIP = 12
KP_LEFT_ANKLE = 15
KP_RIGHT_ANKLE = 16
KP_LEFT_SHOULDER = 5
KP_RIGHT_SHOULDER = 6
KP_LEFT_WRIST = 9
KP_RIGHT_WRIST = 10


class YoloPoseNotReadyError(RuntimeError):
    pass


@dataclass
class PersonDetection:
    """One person instance in pixel coords (frame space)."""

    bbox_xyxy: Tuple[float, float, float, float]  # x1,y1,x2,y2
    conf: float
    # keypoints: (17, 3) → x, y, conf
    keypoints: np.ndarray
    seat_id: Optional[str] = None

    def anchor_xy(self) -> Tuple[float, float]:
        """Seat-mapping anchor: mid-hip if visible, else bbox bottom-center."""
        k = self.keypoints
        hips = []
        for idx in (KP_LEFT_HIP, KP_RIGHT_HIP):
            if idx < len(k) and float(k[idx, 2]) >= 0.25:
                hips.append((float(k[idx, 0]), float(k[idx, 1])))
        if hips:
            xs = [p[0] for p in hips]
            ys = [p[1] for p in hips]
            return sum(xs) / len(xs), sum(ys) / len(ys)
        x1, y1, x2, y2 = self.bbox_xyxy
        return (x1 + x2) / 2.0, y2

    def shoulder_width_px(self) -> Optional[float]:
        k = self.keypoints
        if (
            float(k[KP_LEFT_SHOULDER, 2]) < 0.25
            or float(k[KP_RIGHT_SHOULDER, 2]) < 0.25
        ):
            return None
        dx = float(k[KP_LEFT_SHOULDER, 0] - k[KP_RIGHT_SHOULDER, 0])
        dy = float(k[KP_LEFT_SHOULDER, 1] - k[KP_RIGHT_SHOULDER, 1])
        return float((dx * dx + dy * dy) ** 0.5)

    def torso_yaw_proxy_deg(self) -> Optional[float]:
        """
        Crude Tier-1 facing proxy from shoulder line (not head yaw).

        0 ≈ shoulders level facing camera; sign indicates left/right lean of torso.
        Phase 19 will fuse with MediaPipe yaw'.
        """
        k = self.keypoints
        if (
            float(k[KP_LEFT_SHOULDER, 2]) < 0.25
            or float(k[KP_RIGHT_SHOULDER, 2]) < 0.25
        ):
            return None
        dx = float(k[KP_RIGHT_SHOULDER, 0] - k[KP_LEFT_SHOULDER, 0])
        dy = float(k[KP_RIGHT_SHOULDER, 1] - k[KP_LEFT_SHOULDER, 1])
        # Angle of shoulder line vs horizontal; small |angle| ≈ facing camera
        return float(np.degrees(np.arctan2(dy, dx)))

    def hand_raised(self, *, margin_px: float = 20.0) -> bool:
        """True if either wrist is clearly above its shoulder (image y down)."""
        k = self.keypoints
        for w_i, s_i in (
            (KP_LEFT_WRIST, KP_LEFT_SHOULDER),
            (KP_RIGHT_WRIST, KP_RIGHT_SHOULDER),
        ):
            if float(k[w_i, 2]) < 0.25 or float(k[s_i, 2]) < 0.25:
                continue
            if float(k[w_i, 1]) < float(k[s_i, 1]) - margin_px:
                return True
        return False


_YOLO_CACHE: dict[str, Any] = {}


def load_yolo_pose(weights: str = "yolov8n-pose.pt") -> Any:
    """Load Ultralytics YOLO pose model (cached; auto-downloads weights)."""
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise YoloPoseNotReadyError(
            "ultralytics not installed — pip install -r worker/requirements.txt"
        ) from exc
    from pathlib import Path

    key = str(Path(weights).resolve()) if Path(weights).exists() else str(weights)
    cached = _YOLO_CACHE.get(key)
    if cached is not None:
        logger.info("Reusing cached YOLO pose weights: %s", key)
        return cached
    logger.info("Loading YOLO pose weights: %s", weights)
    model = YOLO(weights)
    # One warm-up predict so first live frame is not a multi-second stall
    try:
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        model.predict(blank, conf=0.25, verbose=False)
    except Exception as exc:  # noqa: BLE001
        logger.warning("YOLO warm-up skipped: %s", exc)
    _YOLO_CACHE[key] = model
    return model


def detect_persons(
    model: Any,
    frame_bgr: np.ndarray,
    *,
    conf: float = 0.25,
    verbose: bool = False,
    imgsz: int = 640,
    max_det: int = 80,
    iou: float = 0.50,
) -> List[PersonDetection]:
    """
    Run pose model on one BGR frame.
    Returns list of PersonDetection (pixel coords).
    """
    if frame_bgr is None or frame_bgr.size == 0:
        return []
    results = model.predict(
        frame_bgr,
        conf=conf,
        verbose=verbose,
        imgsz=int(imgsz),
        max_det=int(max_det),
        iou=float(iou),
    )
    if not results:
        return []
    r0 = results[0]
    people: List[PersonDetection] = []
    boxes = getattr(r0, "boxes", None)
    kps = getattr(r0, "keypoints", None)
    if boxes is None or len(boxes) == 0:
        return []

    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    kp_xy = None
    kp_conf = None
    if kps is not None and kps.xy is not None:
        kp_xy = kps.xy.cpu().numpy()  # (N, 17, 2)
        if kps.conf is not None:
            kp_conf = kps.conf.cpu().numpy()  # (N, 17)
        else:
            kp_conf = np.ones((kp_xy.shape[0], kp_xy.shape[1]), dtype=np.float32)

    for i in range(len(xyxy)):
        x1, y1, x2, y2 = [float(v) for v in xyxy[i]]
        if kp_xy is not None and i < len(kp_xy):
            xy = kp_xy[i]
            cf = kp_conf[i]
            keypoints = np.concatenate(
                [xy, cf.reshape(-1, 1)], axis=1
            ).astype(np.float32)
        else:
            keypoints = np.zeros((17, 3), dtype=np.float32)
        people.append(
            PersonDetection(
                bbox_xyxy=(x1, y1, x2, y2),
                conf=float(confs[i]),
                keypoints=keypoints,
            )
        )
    return people


def warmup_hint() -> str:
    return "YOLOv8-pose: detect_persons + seat assignment (Phase 17)"
