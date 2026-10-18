"""Worker payloads and results read schemas (windows / events)."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


DataQualityLiteral = Literal["insufficient_coverage", "partial_window"]


class WindowPayload(BaseModel):
    start_sec: float
    end_sec: float
    topic_id: Optional[int] = None
    teaching_mode: Optional[str] = None
    expected_regions: Optional[int] = None
    usable_regions: Optional[int] = None
    coverage_pct: Optional[float] = None
    ttoi: Optional[float] = None
    ttoi_lo: Optional[float] = None
    ttoi_hi: Optional[float] = None
    head_down_cue_pct: Optional[float] = None
    hand_raise_events: Optional[int] = None
    candidate_decline: bool = False
    dominant_cue: Optional[str] = None
    data_quality_note: Optional[str] = None


class EventPayload(BaseModel):
    start_sec: float
    end_sec: float
    depth: float
    coverage_pct: Optional[float] = None
    topic_id: Optional[int] = None
    teaching_mode: Optional[str] = None
    dominant_cue: Optional[str] = None
    note: Optional[str] = None


class WorkerResultPayload(BaseModel):
    windows: List[WindowPayload] = Field(default_factory=list)
    events: List[EventPayload] = Field(default_factory=list)


class WindowRead(BaseModel):
    id: int
    session_id: int
    start_sec: float
    end_sec: float
    topic_id: Optional[int] = None
    teaching_mode: Optional[str] = None
    expected_regions: Optional[int] = None
    usable_regions: Optional[int] = None
    coverage_pct: Optional[float] = None
    ttoi: Optional[float] = None
    ttoi_lo: Optional[float] = None
    ttoi_hi: Optional[float] = None
    head_down_cue_pct: Optional[float] = None
    hand_raise_events: Optional[int] = None
    candidate_decline: bool = False
    dominant_cue: Optional[str] = None
    data_quality_note: Optional[str] = None

    model_config = {"from_attributes": True}


class WindowListResponse(BaseModel):
    session_id: int
    items: List[WindowRead]
    total: int
    cached: bool = False


class EventRead(BaseModel):
    id: int
    session_id: int
    start_sec: float
    end_sec: float
    depth: float
    coverage_pct: Optional[float] = None
    topic_id: Optional[int] = None
    teaching_mode: Optional[str] = None
    dominant_cue: Optional[str] = None
    note: Optional[str] = None

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    session_id: int
    items: List[EventRead]
    total: int
