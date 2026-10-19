"""Session request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.enums import SourceType


SourceTypeLiteral = Literal["upload", "webcam", "phone_rtsp"]
SessionStatusLiteral = Literal[
    "draft",
    "ready",
    "analyzing",
    "live",
    "complete",
    "error",
    "purged_video",
]


class SessionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    room_config_id: int = Field(gt=0)
    source_type: SourceTypeLiteral = SourceType.UPLOAD.value
    source_url: Optional[str] = Field(default=None, max_length=1024)
    started_at: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        t = v.strip()
        if not t:
            raise ValueError("Title cannot be empty")
        return t

    @field_validator("source_url")
    @classmethod
    def strip_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        t = v.strip()
        return t or None

    @model_validator(mode="after")
    def phone_requires_url(self) -> "SessionCreate":
        if self.source_type == SourceType.PHONE_RTSP.value and not self.source_url:
            raise ValueError("source_url is required for phone_rtsp sessions")
        return self


class SessionRead(BaseModel):
    id: int
    title: str
    room_config_id: int
    room_name: Optional[str] = None
    source_type: SourceTypeLiteral
    status: SessionStatusLiteral
    source_url: Optional[str] = None
    secondary_source_url: Optional[str] = None
    video_path: Optional[str] = None
    current_mode: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    has_video: bool = False

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    items: List[SessionRead]
    total: int


class SessionSummary(BaseModel):
    """Session analytics header — Redis-backed when warm."""

    session_id: int
    status: SessionStatusLiteral
    mean_ttoi: Optional[float] = None
    mean_coverage: Optional[float] = None
    event_count: int = 0
    window_count: int = 0
    insufficient_coverage_windows: int = 0
    partial_windows: int = 0
    candidate_decline_windows: int = 0
    duration_sec: Optional[float] = None
    cached: bool = False
    note: str = "Summary available after analysis."
