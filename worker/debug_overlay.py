"""
Local-only debug overlays for YOLO + seat regions (not a product export).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import cv2
import numpy as np

from worker.regions import SeatRegion, norm_to_pixel
from worker.seat_mapping import FrameSeatMap, OccupancyCalibration
from worker.vision_yolo import PersonDetection


def draw_seats(
    frame_bgr: np.ndarray,
    seats: Sequence[SeatRegion],
    *,
    occupied_ids: Optional[Sequence[str]] = None,
    color_empty: Tuple[int, int, int] = (180, 180, 80),
    color_occupied: Tuple[int, int, int] = (80, 200, 120),
) -> np.ndarray:
    out = frame_bgr.copy()
    h, w = out.shape[:2]
    occ = set(occupied_ids or [])
    for seat in seats:
        pts = np.array(
            [norm_to_pixel(float(x), float(y), w, h) for x, y in seat.polygon_norm],
            dtype=np.int32,
        )
        col = color_occupied if seat.id in occ else color_empty
        cv2.polylines(out, [pts], isClosed=True, color=col, thickness=2)
        cx, cy = seat.centroid_norm()
        px, py = norm_to_pixel(cx, cy, w, h)
        cv2.putText(
            out,
            seat.id,
            (px - 10, py),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            col,
            1,
            cv2.LINE_AA,
        )
    return out


def draw_persons(
    frame_bgr: np.ndarray,
    persons: Sequence[PersonDetection],
    *,
    draw_skeleton: bool = True,
) -> np.ndarray:
    out = frame_bgr.copy()
    # Ultralytics COCO skeleton edges
    edges = [
        (5, 6),
        (5, 7),
        (7, 9),
        (6, 8),
        (8, 10),
        (5, 11),
        (6, 12),
        (11, 12),
        (11, 13),
        (13, 15),
        (12, 14),
        (14, 16),
    ]
    for p in persons:
        x1, y1, x2, y2 = [int(v) for v in p.bbox_xyxy]
        color = (60, 160, 255) if p.seat_id else (80, 80, 220)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        label = f"{p.conf:.2f}"
        if p.seat_id:
            label = f"{p.seat_id} {label}"
        cv2.putText(
            out,
            label,
            (x1, max(16, y1 - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA,
        )
        ax, ay = p.anchor_xy()
        cv2.circle(out, (int(ax), int(ay)), 4, (0, 255, 255), -1)
        if draw_skeleton and p.keypoints is not None:
            k = p.keypoints
            for a, b in edges:
                if float(k[a, 2]) < 0.25 or float(k[b, 2]) < 0.25:
                    continue
                pt1 = (int(k[a, 0]), int(k[a, 1]))
                pt2 = (int(k[b, 0]), int(k[b, 1]))
                cv2.line(out, pt1, pt2, (200, 200, 50), 1)
            for i in range(len(k)):
                if float(k[i, 2]) < 0.25:
                    continue
                cv2.circle(out, (int(k[i, 0]), int(k[i, 1])), 2, (255, 200, 100), -1)
    return out


def compose_debug_frame(
    frame_bgr: np.ndarray,
    seats: Sequence[SeatRegion],
    frame_map: FrameSeatMap,
    *,
    calibration: Optional[OccupancyCalibration] = None,
    title: str = "",
) -> np.ndarray:
    occupied = calibration.occupied_seat_ids if calibration else [
        sid for sid, idxs in frame_map.seat_to_person_indices.items() if idxs
    ]
    out = draw_seats(frame_bgr, seats, occupied_ids=occupied)
    out = draw_persons(out, frame_map.persons)
    banner = title
    if calibration:
        banner += f"  N_expected={calibration.n_expected}"
    banner += f"  people={len(frame_map.persons)}"
    cv2.putText(
        out,
        banner.strip(),
        (10, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (240, 240, 240),
        2,
        cv2.LINE_AA,
    )
    return out


def encode_live_preview_jpeg(
    frame_bgr: np.ndarray,
    seats: Sequence[SeatRegion],
    frame_map: FrameSeatMap,
    *,
    quality: int = 82,
    max_width: int = 1100,
) -> bytes:
    """JPEG for Console while the worker owns the camera (clarity + overlay)."""
    occupied = [
        sid
        for sid, idxs in frame_map.seat_to_person_indices.items()
        if idxs and not str(sid).startswith("v")
    ]
    out = draw_seats(frame_bgr, seats, occupied_ids=occupied)
    out = draw_persons(out, frame_map.persons, draw_skeleton=False)
    h, w = out.shape[:2]
    if w > max_width > 0:
        scale = max_width / float(w)
        out = cv2.resize(
            out,
            (max_width, max(1, int(h * scale))),
            interpolation=cv2.INTER_AREA,
        )
    n = len(frame_map.persons)
    seated = sum(1 for v in frame_map.seat_to_person_indices.values() if v)
    # Hershey fonts: stick to plain ASCII (no pipes / unicode)
    label = f"Live - {n} people - {seated} tracked"
    cv2.putText(
        out,
        label,
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (245, 245, 245),
        2,
        cv2.LINE_AA,
    )
    ok, buf = cv2.imencode(
        ".jpg",
        out,
        [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)],
    )
    if not ok:
        return b""
    return bytes(buf)


def write_debug_image(path: Path | str, image_bgr: np.ndarray) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(out), image_bgr)
    if not ok:
        raise RuntimeError(f"Failed to write debug image: {out}")
    return out.resolve()


def write_debug_video(
    path: Path | str,
    frames_bgr: Sequence[np.ndarray],
    *,
    fps: float = 2.0,
) -> Path:
    if not frames_bgr:
        raise ValueError("No frames to write")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    h, w = frames_bgr[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out), fourcc, fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for {out}")
    try:
        for fr in frames_bgr:
            if fr.shape[0] != h or fr.shape[1] != w:
                fr = cv2.resize(fr, (w, h))
            writer.write(fr)
    finally:
        writer.release()
    return out.resolve()
