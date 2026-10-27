"""Live lecture cockpit schemas."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class LiveStartBody(BaseModel):
    """Phone browsers set this so the worker reads frames from the phone, not OpenCV."""

    browser_camera: bool = False


class LiveSeatStat(BaseModel):
    seat_id: str
    orientation_pct: Optional[float] = None
    usable: bool = False


class LiveGroup(BaseModel):
    label: str
    seat_ids: List[str] = Field(default_factory=list)
    orientation_pct: Optional[float] = None
    kind: str = "decline_cluster"


class LiveAlert(BaseModel):
    kind: str
    start_sec: float
    end_sec: Optional[float] = None
    message: Optional[str] = None
    group_label: Optional[str] = None
    seat_ids: List[str] = Field(default_factory=list)


class LiveState(BaseModel):
    session_id: int
    status: str
    running: bool
    job_id: Optional[int] = None
    elapsed_sec: float = 0.0
    window_seconds: float = 30.0
    next_window_in_sec: Optional[float] = None
    ttoi: Optional[float] = None
    coverage_pct: Optional[float] = None
    usable_seats: Optional[int] = None
    expected_seats: Optional[int] = None
    persons_detected: Optional[int] = None
    persons_in_seats: Optional[int] = None
    per_seat: List[LiveSeatStat] = Field(default_factory=list)
    groups: List[LiveGroup] = Field(default_factory=list)
    alerts: List[LiveAlert] = Field(default_factory=list)
    updated_at: Optional[str] = None
    secondary_source_url: Optional[str] = None
    message: Optional[str] = None
    detection_hint: Optional[str] = None
    preview_available: bool = False


class EventFeedbackBody(BaseModel):
    feedback: Literal["useful", "false_alarm", "insufficient"]


class SecondarySourceBody(BaseModel):
    secondary_source_url: Optional[str] = Field(default=None, max_length=1024)
