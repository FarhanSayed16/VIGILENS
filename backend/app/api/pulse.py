"""Public pulse stub — full implementation in Phase 14."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["pulse"])


class PulseStubRequest(BaseModel):
    score_1_to_5: int = Field(ge=1, le=5)


@router.post("/pulse/{session_id}")
def pulse_stub(session_id: int, body: PulseStubRequest) -> dict:
    """
    Public (no JWT). Phase 14 will persist to DB and stamp topic_id.
    Rejects any extra identity fields by schema (score only).
    """
    return {
        "status": "accepted_stub",
        "session_id": session_id,
        "score_1_to_5": body.score_1_to_5,
        "message": "Pulse persistence arrives in Phase 14.",
    }
