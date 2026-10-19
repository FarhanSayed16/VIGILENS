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
            "OpenCV not available for detect — use seat grid instead",
            status_code=503,
            code="opencv_unavailable",
        ) from exc

    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise AppError("Could not decode image", status_code=400, code="bad_image")

    layout = quick_calibrate.suggest_layout(placement, rows=rows, cols=cols)
    message: Optional[str] = None
    seats = layout["seat_regions"]
    people_found = 0

    try:
        detected = quick_calibrate.detect_people_seats(image)
        people_found = len(detected)
        if people_found > 0:
            seats = detected
        else:
            message = (
                "No people detected — kept the seat grid for this viewpoint. "
                "Have students sit in view, or adjust the grid."
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("YOLO detect failed, using grid: %s", type(exc).__name__)
        message = (
            f"Person detect unavailable ({type(exc).__name__}) — using seat grid. "
            "Install worker deps or draw seats in Advanced."
        )

    if people_found > 0 and layout.get("facing_mode") == "toward_camera":
        message = (
            message
            or f"Detected {people_found} person(s) as seats only — "
            "no board box (toward-camera mode)."
        )

    return CalibrateDetectResponse(
        placement=placement,  # type: ignore[arg-type]
        seat_regions=seats,
        target_roi=layout["target_roi"],
        facing_mode=layout.get("facing_mode") or "toward_board",
        hint=layout["hint"],
        people_found=people_found,
        message=message,
    )
