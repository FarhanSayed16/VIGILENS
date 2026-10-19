"""Room config request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class BoxRegion(BaseModel):
    type: Literal["box"] = "box"
    id: str = Field(min_length=1, max_length=64)
    label: Optional[str] = Field(default=None, max_length=128)
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    w: float = Field(gt=0.0, le=1.0)
    h: float = Field(gt=0.0, le=1.0)

    @model_validator(mode="after")
    def fits_frame(self) -> "BoxRegion":
        if self.x + self.w > 1.0001 or self.y + self.h > 1.0001:
            raise ValueError("Box extends outside normalized frame [0,1]")
        return self


class PolygonRegion(BaseModel):
    type: Literal["polygon"] = "polygon"
    id: str = Field(min_length=1, max_length=64)
    label: Optional[str] = Field(default=None, max_length=128)
    points: List[List[float]] = Field(min_length=3)

    @field_validator("points")
    @classmethod
    def valid_points(cls, points: List[List[float]]) -> List[List[float]]:
        for pt in points:
            if len(pt) != 2:
                raise ValueError("Each point must be [x, y]")
            x, y = pt
            if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
                raise ValueError("Polygon points must be in [0,1]")
        return points


SeatRegion = Annotated[Union[BoxRegion, PolygonRegion], Field(discriminator="type")]
TargetRoi = Annotated[Union[BoxRegion, PolygonRegion], Field(discriminator="type")]


class CameraDefaults(BaseModel):
    preferred_source: Optional[Literal["upload", "webcam", "phone_rtsp"]] = "upload"
    webcam_index: Optional[int] = Field(default=0, ge=0, le=10)
    phone_url_example: Optional[str] = Field(default=None, max_length=1024)
    # Quick-calibrate viewpoint (back_of_room | facing_class | left_side | right_side)
    placement: Optional[str] = Field(default=None, max_length=32)
    # toward_camera = no in-frame board; students looking at lens count as oriented
    facing_mode: Optional[str] = Field(default=None, max_length=32)


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    seat_regions: List[SeatRegion] = Field(default_factory=list)
    target_roi: Optional[TargetRoi] = None
    camera_defaults: Optional[CameraDefaults] = None


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    seat_regions: Optional[List[SeatRegion]] = None
    target_roi: Optional[TargetRoi] = None
    camera_defaults: Optional[CameraDefaults] = None


class RoomRead(BaseModel):
    id: int
    name: str
    seat_regions: List[Any]
    target_roi: Optional[Any] = None
    camera_defaults: Optional[Any] = None
    created_at: datetime
    seat_count: int = 0

    model_config = {"from_attributes": True}
