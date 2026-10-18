"""Candidate orientation decline events — JWT required."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.results import EventListResponse
from app.services import result_service

router = APIRouter(prefix="/sessions/{session_id}/events", tags=["events"])


@router.get("", response_model=EventListResponse)
def list_events(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> EventListResponse:
    return result_service.list_events(db, session_id)
