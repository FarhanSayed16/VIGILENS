"""Anonymous pulse schemas — score only, no PII."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PulseSubmit(BaseModel):
    """Public body: score only. Extra fields (name, seat, …) are rejected."""

    model_config = ConfigDict(extra="forbid")

    score_1_to_5: int = Field(ge=1, le=5)


class PulseAccepted(BaseModel):
    status: str = "accepted"
    session_id: int
    score_1_to_5: int
    topic_id: Optional[int] = None
    created_at: datetime
    message: str = "Thanks - anonymous response recorded."
