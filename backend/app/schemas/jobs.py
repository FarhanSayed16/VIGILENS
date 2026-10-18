"""Analysis job request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


JobStatusLiteral = Literal["queued", "running", "done", "error", "cancelled"]
StageLiteral = Literal[
    "queued", "ingest", "vision", "aggregate", "done", "error", "cancelled"
]


class JobRead(BaseModel):
    id: int
    session_id: int
    status: JobStatusLiteral
    progress_pct: float = 0.0
    stage: Optional[StageLiteral] = None
    error_message: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AnalysisStartResponse(JobRead):
    message: str = Field(
        default="Analysis job started. Poll GET /jobs/{id} for progress."
    )
