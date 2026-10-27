"""Quick calibration: viewpoint presets + optional YOLO person→seat detect."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.exceptions import AppError
from app.schemas.calibrate import (
    CalibrateDetectResponse,
    CalibrateSuggestBody,
    CalibrateSuggestResponse,
)

logger = logging.getLogger(__name__)

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def suggest_layout(body: CalibrateSuggestBody) -> CalibrateSuggestResponse:
    from worker import quick_calibrate

    try:
        raw = quick_calibrate.suggest_layout(
            body.placement, rows=body.rows, cols=body.cols
        )
    except ValueError as exc:
        raise AppError(str(exc), status_code=400, code="bad_placement") from exc
    return CalibrateSuggestResponse(**raw)


def detect_from_bytes(
    data: bytes,
    *,
    placement: str,
    rows: int = 3,
    cols: int = 4,
) -> CalibrateDetectResponse:
    from worker import quick_calibrate

    if placement not in quick_calibrate.PLACEMENTS:
        raise AppError("Unknown camera placement", status_code=400, code="bad_placement")

    try:
        import cv2
    except ImportError as exc:
        raise AppError(
            "OpenCV is not available, so this frame cannot be checked",
            status_code=503,
            code="opencv_unavailable",
        ) from exc

    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise AppError("Could not decode image", status_code=400, code="bad_image")

    layout = quick_calibrate.suggest_layout(placement, rows=rows, cols=cols)
    message = (
        "Seats are not drawn here. When the lecture starts, each stable face "
        "with both eyes becomes its own seat."
    )
    del image

    return CalibrateDetectResponse(
        placement=placement,  # type: ignore[arg-type]
        seat_regions=[],
        target_roi=layout["target_roi"],
        facing_mode=layout.get("facing_mode") or "toward_board",
        hint=layout["hint"],
        people_found=0,
        message=message,
    )
