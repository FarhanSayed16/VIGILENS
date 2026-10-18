"""Topic marker schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TopicCreate(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    start_sec: Optional[float] = Field(default=None, ge=0)
    end_sec: Optional[float] = Field(default=None, ge=0)

    @field_validator("label")
    @classmethod
    def strip_label(cls, v: str) -> str:
        t = v.strip()
        if not t:
            raise ValueError("Label cannot be empty")
        return t

    @field_validator("end_sec")
    @classmethod
    def end_after_start(cls, v: Optional[float], info) -> Optional[float]:
        start = info.data.get("start_sec")
        if v is not None and start is not None and v < start:
            raise ValueError("end_sec must be >= start_sec")
        return v


class TopicRead(BaseModel):
    id: int
    session_id: int
    start_sec: float
    end_sec: Optional[float] = None
    label: str

    model_config = {"from_attributes": True}


class TopicListResponse(BaseModel):
    items: List[TopicRead]
    total: int
