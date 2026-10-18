"""Public anonymous pulse — score only, rate-limited, topic stamped server-side."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.deps.db import get_db
from app.schemas.pulse import PulseAccepted, PulseSubmit
from app.services import pulse_service

router = APIRouter(tags=["pulse"])


@router.post("/pulse/{session_id}", response_model=PulseAccepted)
def submit_pulse(
    session_id: int,
    body: PulseSubmit,
    request: Request,
    db: Session = Depends(get_db),
) -> PulseAccepted:
    return pulse_service.submit_pulse(db, session_id, body, request)
