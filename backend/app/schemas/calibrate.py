"""Quick room calibration request/response schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Placement = Literal["back_of_room", "facing_class", "left_side", "right_side"]


class CalibrateSuggestBody(BaseModel):
    placement: Placement
    rows: int = Field(default=3, ge=1, le=12)
    cols: int = Field(default=4, ge=1, le=12)


class CalibrateSuggestResponse(BaseModel):
    placement: Placement
    seat_regions: List[Dict[str, Any]]
    target_roi: Optional[Dict[str, Any]] = None
    facing_mode: str = "toward_board"
    hint: str
    mode: str = "grid"


class CalibrateDetectResponse(BaseModel):
    placement: Placement
    seat_regions: List[Dict[str, Any]]
    target_roi: Optional[Dict[str, Any]] = None
    facing_mode: str = "toward_board"
    hint: str
    mode: str = "detect"
    people_found: int
    message: Optional[str] = None
