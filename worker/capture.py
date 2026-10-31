"""
Video ingest — MP4 file, webcam index, or phone RTSP/HTTP URL.

Samples frames at ~1–2 fps (from config) without running CV models yet.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generator, Iterator, List, Optional, Tuple, Union

import cv2
import numpy as np

from worker.config import load_config, sampling_fps

logger = logging.getLogger(__name__)

SourceRef = Union[str, Path, int]


@dataclass
class SampledFrame:
    """One sampled frame from the source."""

    index: int  # ordinal among sampled frames (0-based)
    frame_index: int  # original video frame index when known
    time_sec: float
    image: np.ndarray  # BGR uint8 HxWx3
    width: int
    height: int


@dataclass
class CaptureInfo:
    source: str
    source_kind: str  # file | webcam | stream
    fps_native: float
    frame_count: Optional[int]
    width: int
    height: int
    sample_fps: float


def frame_mean_luma(frame: np.ndarray) -> float:
    """0–255 average brightness — near 0 usually means black / locked camera."""
    if frame is None or frame.size == 0:
        return 0.0
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))


def enhance_for_detection(frame_bgr: np.ndarray) -> np.ndarray:
    """Mild CLAHE — helps YOLO in dim desk lighting without inventing people."""
    if frame_bgr is None or frame_bgr.size == 0:
        return frame_bgr
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    merged = cv2.merge([clahe.apply(l), a, b])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def _open_webcam_index(idx: int) -> cv2.VideoCapture:
    """Windows: DirectShow first; warm up and prefer a non-black feed."""
    cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(idx)
    if not cap.isOpened():
        return cap
    # Prefer a usable size for pose
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    # Discard driver warm-up frames
    for _ in range(8):
        cap.read()
    return cap


def resolve_webcam_source(
    preferred: int = 0,
    *,
    max_index: int = 3,
) -> tuple[str, float]:
    """
    Pick a webcam index that yields a non-black frame.

    Returns (source_url like 'webcam:0', mean_luma). Raises if all black/unavailable.
    """
    order = [preferred] + [i for i in range(0, max_index + 1) if i != preferred]
    best: Optional[tuple[int, float]] = None
    for idx in order:
        cap = _open_webcam_index(idx)
        try:
            if not cap.isOpened():
                continue
            ok, frame = cap.read()
            if not ok or frame is None:
                continue
            luma = frame_mean_luma(frame)
            logger.info("Webcam probe index=%s luma=%.1f shape=%s", idx, luma, getattr(frame, "shape", None))
            if luma < 8.0:
                continue
            if best is None or luma > best[1]:
                best = (idx, luma)
            # Good enough — prefer preferred if usable
            if idx == preferred and luma >= 20.0:
                return f"webcam:{idx}", luma
        finally:
            cap.release()
    if best is None:
        raise RuntimeError(
            "Could not open a usable webcam (all black or locked). "
            "Close other apps using the camera (including the browser preview), "
            "then Start lecture again."
        )
    return f"webcam:{best[0]}", best[1]


def _open_capture(source: SourceRef) -> tuple[cv2.VideoCapture, str, str]:
    """
    Open OpenCV VideoCapture.
    source: path string, Path, webcam int, or URL (rtsp/http).
    """
    if isinstance(source, int):
        cap = _open_webcam_index(source)
        return cap, f"webcam:{source}", "webcam"

    s = str(source)
    lower = s.lower()
    if lower.startswith("webcam:"):
        idx = int(s.split(":", 1)[1])
        return _open_capture(idx)

    if lower.startswith(("rtsp://", "http://", "https://")):
        cap = cv2.VideoCapture(s)
        return cap, s, "stream"

    path = Path(s)
    if not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")
    cap = cv2.VideoCapture(str(path))
    return cap, str(path.resolve()), "file"


def probe_source(source: SourceRef, *, config_path: Optional[str] = None) -> CaptureInfo:
    """Open briefly and read metadata (does not keep handle open)."""
    cfg = load_config(config_path) if config_path else load_config()
    target_fps = sampling_fps(cfg)
    cap, label, kind = _open_capture(source)
    try:
        if not cap.isOpened():
            raise RuntimeError(f"Could not open capture source: {label}")
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        return CaptureInfo(
            source=label,
            source_kind=kind,
            fps_native=fps if fps > 1e-3 else 0.0,
            frame_count=count if count > 0 else None,
            width=w,
            height=h,
            sample_fps=target_fps,
        )
    finally:
        cap.release()


def iter_sampled_frames(
    source: SourceRef,
    *,
    sample_fps: Optional[float] = None,
    max_frames: Optional[int] = None,
    config_path: Optional[str] = None,
) -> Generator[SampledFrame, None, None]:
    """
    Yield frames sampled at approximately `sample_fps`.

    For files: seeks by time when possible; falls back to skip-stride.
    For webcam/stream: wall-clock pacing between grabs.
    """
    cfg = load_config(config_path) if config_path else load_config()
    target = float(sample_fps if sample_fps is not None else sampling_fps(cfg))
    target = max(0.1, target)

    cap, label, kind = _open_capture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open capture source: {label}")

    try:
        native_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        if native_fps < 1e-3:
            native_fps = 25.0 if kind == "file" else target

        interval = 1.0 / target
        sampled = 0
        next_t = 0.0

        if kind == "file":
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            duration = (total / native_fps) if total > 0 else None
            while True:
                if max_frames is not None and sampled >= max_frames:
                    break
                if duration is not None and next_t > duration + 1e-6:
                    break
                # Seek by msec
                cap.set(cv2.CAP_PROP_POS_MSEC, next_t * 1000.0)
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                frame_idx = int(cap.get(cv2.CAP_PROP_POS_FRAMES) or 0)
                h, w = frame.shape[:2]
                yield SampledFrame(
                    index=sampled,
                    frame_index=max(0, frame_idx - 1),
                    time_sec=round(next_t, 3),
                    image=frame,
                    width=w,
                    height=h,
                )
                sampled += 1
                next_t += interval
        else:
            # Live sources: grab sequentially, keep every ~interval by timestamp
            import time

            t0 = time.monotonic()
            frame_i = 0
            while True:
                if max_frames is not None and sampled >= max_frames:
                    break
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                elapsed = time.monotonic() - t0
                if elapsed + 1e-6 < next_t and sampled > 0:
                    frame_i += 1
                    continue
                h, w = frame.shape[:2]
                yield SampledFrame(
                    index=sampled,
                    frame_index=frame_i,
                    time_sec=round(elapsed, 3),
                    image=frame,
                    width=w,
                    height=h,
                )
                sampled += 1
                next_t = sampled * interval
                frame_i += 1
    finally:
        cap.release()


def iter_pushed_jpegs(
    pull: Callable[[], Tuple[Optional[bytes], int]],
    *,
    sample_fps: float = 12.0,
    should_stop: Optional[Callable[[], bool]] = None,
    on_waiting: Optional[Callable[[str], None]] = None,
) -> Generator[SampledFrame, None, None]:
    """
    Frames posted by a phone browser (JPEG bytes), not an OpenCV device.

    Blocks until Stop. A missing camera does not raise — the phone may still
    be showing the permission prompt.
    """
    import time

    target = max(1.0, float(sample_fps))
    interval = 1.0 / target
    t0 = time.monotonic()
    last_seq = -1
    sampled = 0
    next_t = 0.0
    last_wait_note = 0.0

    while True:
        if should_stop and should_stop():
            return
        jpeg, seq = pull()
        now = time.monotonic() - t0
        if jpeg and seq != last_seq and now + 1e-6 >= next_t:
            arr = np.frombuffer(jpeg, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            last_seq = seq
            if frame is None:
                time.sleep(0.04)
                continue
            h, w = frame.shape[:2]
            yield SampledFrame(
                index=sampled,
                frame_index=sampled,
                time_sec=round(now, 3),
                image=frame,
                width=w,
                height=h,
            )
            sampled += 1
            next_t = now + interval
            continue
        if sampled == 0 and on_waiting and now - last_wait_note > 3.0:
            last_wait_note = now
            on_waiting(
                "Waiting for this phone's camera. Tap Allow camera on the phone."
            )
        time.sleep(0.04)


def collect_sample_timestamps(
    source: SourceRef,
    *,
    sample_fps: Optional[float] = None,
    max_frames: Optional[int] = None,
    config_path: Optional[str] = None,
) -> List[float]:
    """Lightweight pass: timestamps only (still decodes frames)."""
    return [
        f.time_sec
        for f in iter_sampled_frames(
            source,
            sample_fps=sample_fps,
            max_frames=max_frames,
            config_path=config_path,
        )
    ]


def write_synthetic_clip(
    path: Path | str,
    *,
    duration_sec: float = 3.0,
    fps: float = 10.0,
    width: int = 640,
    height: int = 360,
) -> Path:
    """
    Write a short synthetic MP4 for local smoke tests (no classroom video in git).
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Could not open VideoWriter for {out}")
    n = max(1, int(duration_sec * fps))
    try:
        for i in range(n):
            # Simple moving bar — enough to decode + sample
            img = np.zeros((height, width, 3), dtype=np.uint8)
            img[:] = (40, 50, 45)
            x = int((i / max(1, n - 1)) * (width - 40))
            cv2.rectangle(img, (x, height // 3), (x + 40, 2 * height // 3), (80, 180, 140), -1)
            cv2.putText(
                img,
                f"t={i / fps:.1f}s",
                (16, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (220, 220, 220),
                1,
                cv2.LINE_AA,
            )
            writer.write(img)
    finally:
        writer.release()
    return out.resolve()
