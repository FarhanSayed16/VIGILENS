"""Teaching mode change schemas."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


ModeLiteral = Literal["explanation", "note_taking", "qa", "discussion"]


class ModeChangeCreate(BaseModel):
    mode: ModeLiteral
    start_sec: Optional[float] = Field(default=None, ge=0)


class ModeChangeRead(BaseModel):
    id: int
    session_id: int
    start_sec: float
    mode: ModeLiteral

    model_config = {"from_attributes": True}


class ModeChangeListResponse(BaseModel):
    items: List[ModeChangeRead]
    total: int
    current_mode: Optional[ModeLiteral] = None
