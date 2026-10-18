"""Media upload and source attachment schemas."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.enums import SourceType


SourceTypeLiteral = Literal["upload", "webcam", "phone_rtsp"]


class SourceUpdate(BaseModel):
    """Attach webcam device hint or phone stream URL (no file body)."""

    source_type: SourceTypeLiteral
    source_url: Optional[str] = Field(default=None, max_length=1024)
    webcam_index: Optional[int] = Field(default=None, ge=0, le=10)

    @field_validator("source_url")
    @classmethod
    def strip_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        t = v.strip()
        return t or None

    @model_validator(mode="after")
    def validate_source(self) -> "SourceUpdate":
        if self.source_type == SourceType.PHONE_RTSP.value and not self.source_url:
            raise ValueError("source_url is required for phone_rtsp")
        if self.source_type == SourceType.WEBCAM.value:
            # Prefer explicit webcam_index; fall back to numeric source_url
            if self.webcam_index is None and self.source_url:
                try:
                    self.webcam_index = int(self.source_url.replace("webcam:", ""))
                except ValueError as exc:
                    raise ValueError(
                        "webcam source_url must be an index or webcam:<n>"
                    ) from exc
            if self.webcam_index is None:
                self.webcam_index = 0
            self.source_url = f"webcam:{self.webcam_index}"
        if self.source_type == SourceType.UPLOAD.value:
            # Upload type without a file just records preference; video via POST /upload
            pass
        return self


class UploadResult(BaseModel):
    session_id: int
    filename: str
    size_bytes: int
    content_type: Optional[str] = None
    has_video: bool = True
    status: str
    relative_path: str
