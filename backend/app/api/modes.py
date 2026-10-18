"""Teaching mode changes nested under sessions — JWT required."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.modes import ModeChangeCreate, ModeChangeListResponse, ModeChangeRead
from app.services import mode_service

router = APIRouter(tags=["modes"])


@router.get(
    "/sessions/{session_id}/modes",
    response_model=ModeChangeListResponse,
)
def list_modes(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> ModeChangeListResponse:
    return mode_service.list_modes(db, session_id)


@router.post(
    "/sessions/{session_id}/mode",
    response_model=ModeChangeRead,
    status_code=201,
)
def set_mode(
    session_id: int,
    body: ModeChangeCreate,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> ModeChangeRead:
    return mode_service.set_mode(db, session_id, body)
