"""
MediaPipe Face Landmarker Tier-2 head pose (Task API + solvePnP).

Convention (verified by smoke_head_pose.py):
- yaw_deg  > 0 → head turned toward image-right (subject looking right)
- pitch_deg > 0 → head tilted down (chin toward chest)
- face below face_width_min_px → None (caller falls back to Tier-1)
"""

from __future__ import annotations

import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

import cv2
import numpy as np

from worker.config import REPO_ROOT

logger = logging.getLogger(__name__)

# FaceMesh / Face Landmarker topology indices (478-point)
IDX_NOSE = 1
IDX_CHIN = 152
IDX_LEFT_EYE_OUTER = 33
IDX_RIGHT_EYE_OUTER = 263
IDX_MOUTH_LEFT = 61
IDX_MOUTH_RIGHT = 291
IDX_2D = (
    IDX_NOSE,
    IDX_CHIN,
    IDX_LEFT_EYE_OUTER,
    IDX_RIGHT_EYE_OUTER,
    IDX_MOUTH_LEFT,
    IDX_MOUTH_RIGHT,
)

# Generic 3D head model (mm-scale) paired with IDX_2D
MODEL_3D = np.array(
    [
        (0.0, 0.0, 0.0),  # nose tip
        (0.0, -330.0, -65.0),  # chin
        (-225.0, 170.0, -135.0),  # left eye outer
        (225.0, 170.0, -135.0),  # right eye outer
        (-150.0, -150.0, -125.0),  # left mouth
        (150.0, -150.0, -125.0),  # right mouth
    ],
    dtype=np.float64,
)

DEFAULT_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
DEFAULT_MODEL_PATH = REPO_ROOT / "models" / "face_landmarker.task"


class MediaPipeNotReadyError(RuntimeError):
    pass


@dataclass
class HeadPoseResult:
    yaw_deg: float
    pitch_deg: float
    roll_deg: float
    face_width_px: float
    # Pixel landmarks used for PnP (6x2)
    pnp_points_px: np.ndarray


def ensure_face_landmarker_model(
    model_path: Optional[str | Path] = None,
    *,
    url: str = DEFAULT_MODEL_URL,
) -> Path:
    """Download Face Landmarker .task bundle if missing."""
    from worker.config import resolve_model_path

    if model_path:
        path = resolve_model_path(model_path)
    else:
        path = DEFAULT_MODEL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.stat().st_size > 10_000:
        return path
    logger.info("Downloading Face Landmarker model → %s", path)
    urllib.request.urlretrieve(url, str(path))
    if not path.is_file() or path.stat().st_size < 10_000:
        raise MediaPipeNotReadyError(f"Failed to download Face Landmarker model: {path}")
    return path


def load_face_landmarker(
    model_path: Optional[str | Path] = None,
    *,
    num_faces: int = 5,
) -> Any:
    """Create Face Landmarker via Task API (not legacy solutions.face_mesh)."""
    try:
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import (
            FaceLandmarker,
            FaceLandmarkerOptions,
            RunningMode,
        )
    except ImportError as exc:
        raise MediaPipeNotReadyError(
            "mediapipe not installed — pip install -r worker/requirements.txt"
        ) from exc

    path = ensure_face_landmarker_model(model_path)
    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(path)),
        running_mode=RunningMode.IMAGE,
        num_faces=max(1, num_faces),
        output_facial_transformation_matrixes=False,
    )
    return FaceLandmarker.create_from_options(options)


def landmarks_to_px(
    landmarks: Sequence[Any],
    width: int,
    height: int,
) -> np.ndarray:
    """Normalized MediaPipe landmarks → (N, 2) pixel xy."""
    pts = np.zeros((len(landmarks), 2), dtype=np.float64)
    for i, lm in enumerate(landmarks):
        pts[i, 0] = float(lm.x) * width
        pts[i, 1] = float(lm.y) * height
    return pts


def face_width_px_from_landmarks(lm_px: np.ndarray) -> float:
    """Inter-outer-eye distance in pixels (face width proxy)."""
    left = lm_px[IDX_LEFT_EYE_OUTER]
    right = lm_px[IDX_RIGHT_EYE_OUTER]
    return float(np.linalg.norm(right - left))


def camera_matrix(width: int, height: int) -> np.ndarray:
    f = float(width)
    return np.array(
        [[f, 0.0, width / 2.0], [0.0, f, height / 2.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )


def head_pose_from_landmarks_px(
    lm_px: np.ndarray,
    width: int,
    height: int,
) -> Optional[Tuple[float, float, float]]:
    """
    solvePnP → (yaw_deg, pitch_deg, roll_deg) with enforced sign convention.

    Returns None if PnP fails.
    """
    if lm_px.shape[0] <= max(IDX_2D):
        return None
    pts = np.array([lm_px[i] for i in IDX_2D], dtype=np.float64)
    cam = camera_matrix(width, height)
    ok, rvec, _tvec = cv2.solvePnP(
        MODEL_3D,
        pts,
        cam,
        None,
        flags=cv2.SOLVEPNP_ITERATIVE,
    )
    if not ok:
        return None
    rmat, _ = cv2.Rodrigues(rvec)
    angles, *_ = cv2.RQDecomp3x3(rmat)
    # Starting unwrap from product docs — signs verified by smoke_head_pose.py
    pitch_raw, yaw_raw, roll_raw = [((float(a) + 90.0) % 180.0) - 90.0 for a in angles]

    # Convention (synthetic L/R/U/D round-trip):
    # +yaw = image-right, +pitch = look down
    yaw = float(yaw_raw)
    pitch = float(pitch_raw)
    roll = float(roll_raw)
    return yaw, pitch, roll


def detect_faces_landmarks(
    landmarker: Any,
    frame_bgr: np.ndarray,
) -> List[np.ndarray]:
    """
    Run Face Landmarker on a BGR frame.
    Returns list of (N, 2) landmark arrays in pixel coords.
    """
    import mediapipe as mp

    if frame_bgr is None or frame_bgr.size == 0:
        return []
    h, w = frame_bgr.shape[:2]
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect(mp_image)
    faces: List[np.ndarray] = []
    if not result.face_landmarks:
        return faces
    for face in result.face_landmarks:
        faces.append(landmarks_to_px(face, w, h))
    return faces


def estimate_head_pose(
    landmarker: Any,
    frame_bgr: np.ndarray,
    *,
    face_width_min_px: float = 80.0,
    face_index: int = 0,
) -> Optional[HeadPoseResult]:
    """
    Return HeadPoseResult for one face, or None if missing / too small / PnP fails.
    """
    faces = detect_faces_landmarks(landmarker, frame_bgr)
    if not faces or face_index >= len(faces):
        return None
    h, w = frame_bgr.shape[:2]
    lm_px = faces[face_index]
    fw = face_width_px_from_landmarks(lm_px)
    if fw < face_width_min_px:
        return None
    pose = head_pose_from_landmarks_px(lm_px, w, h)
    if pose is None:
        return None
    yaw, pitch, roll = pose
    pnp_pts = np.array([lm_px[i] for i in IDX_2D], dtype=np.float64)
    return HeadPoseResult(
        yaw_deg=yaw,
        pitch_deg=pitch,
        roll_deg=roll,
        face_width_px=fw,
        pnp_points_px=pnp_pts,
    )


def estimate_head_poses_all(
    landmarker: Any,
    frame_bgr: np.ndarray,
    *,
    face_width_min_px: float = 80.0,
) -> List[HeadPoseResult]:
    """All faces that pass the width gate and PnP."""
    faces = detect_faces_landmarks(landmarker, frame_bgr)
    if not faces:
        return []
    h, w = frame_bgr.shape[:2]
    out: List[HeadPoseResult] = []
    for lm_px in faces:
        fw = face_width_px_from_landmarks(lm_px)
        if fw < face_width_min_px:
            continue
        pose = head_pose_from_landmarks_px(lm_px, w, h)
        if pose is None:
            continue
        yaw, pitch, roll = pose
        out.append(
            HeadPoseResult(
                yaw_deg=yaw,
                pitch_deg=pitch,
                roll_deg=roll,
                face_width_px=fw,
                pnp_points_px=np.array([lm_px[i] for i in IDX_2D], dtype=np.float64),
            )
        )
    return out


def project_model_with_yaw_pitch(
    yaw_deg: float,
    pitch_deg: float,
    width: int = 640,
    height: int = 480,
    *,
    distance: float = 600.0,
) -> np.ndarray:
    """
    Project MODEL_3D with known yaw/pitch for sign tests.

    Uses the same convention as head_pose_from_landmarks_px:
    +yaw → image-right, +pitch → look down.
    Returns (6, 2) image points for IDX_2D order.
    """
    # Rotation: pitch about X, yaw about Y (OpenCV camera: +X right, +Y down, +Z forward)
    yaw = np.radians(yaw_deg)
    pitch = np.radians(pitch_deg)
    Rx = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, np.cos(pitch), -np.sin(pitch)],
            [0.0, np.sin(pitch), np.cos(pitch)],
        ],
        dtype=np.float64,
    )
    Ry = np.array(
        [
            [np.cos(yaw), 0.0, np.sin(yaw)],
            [0.0, 1.0, 0.0],
            [-np.sin(yaw), 0.0, np.cos(yaw)],
        ],
        dtype=np.float64,
    )
    R = Ry @ Rx
    rvec, _ = cv2.Rodrigues(R)
    tvec = np.array([[0.0], [0.0], [distance]], dtype=np.float64)
    cam = camera_matrix(width, height)
    img_pts, _ = cv2.projectPoints(MODEL_3D, rvec, tvec, cam, None)
    return img_pts.reshape(-1, 2).astype(np.float64)


def verify_solvpnp_sign_convention(*, tol_deg: float = 12.0) -> List[str]:
    """
    Round-trip known yaw/pitch through projectPoints → solvePnP.
    Returns list of failure messages (empty = OK).
    """
    failures: List[str] = []
    w, h = 640, 480
    cases = [
        ("look_right", 25.0, 0.0, +1, 0),
        ("look_left", -25.0, 0.0, -1, 0),
        ("look_down", 0.0, 20.0, 0, +1),
        ("look_up", 0.0, -20.0, 0, -1),
    ]
    for name, yaw_t, pitch_t, yaw_sign, pitch_sign in cases:
        # Build synthetic full landmark array with only PnP indices filled
        pts6 = project_model_with_yaw_pitch(yaw_t, pitch_t, w, h)
        lm = np.zeros((478, 2), dtype=np.float64)
        for j, idx in enumerate(IDX_2D):
            lm[idx] = pts6[j]
        recovered = head_pose_from_landmarks_px(lm, w, h)
        if recovered is None:
            failures.append(f"{name}: PnP failed")
            continue
        yaw_r, pitch_r, _roll = recovered
        if yaw_sign != 0 and np.sign(yaw_r) != yaw_sign:
            failures.append(f"{name}: yaw sign got {yaw_r:.1f}, want sign {yaw_sign}")
        if pitch_sign != 0 and np.sign(pitch_r) != pitch_sign:
            failures.append(
                f"{name}: pitch sign got {pitch_r:.1f}, want sign {pitch_sign}"
            )
        if abs(yaw_r - yaw_t) > tol_deg:
            failures.append(f"{name}: yaw {yaw_r:.1f} vs target {yaw_t:.1f}")
        if abs(pitch_r - pitch_t) > tol_deg:
            failures.append(f"{name}: pitch {pitch_r:.1f} vs target {pitch_t:.1f}")
    return failures


def warmup_hint() -> str:
    return "Phase 18: Face Landmarker Task API + face-width gate + solvePnP yaw/pitch"
