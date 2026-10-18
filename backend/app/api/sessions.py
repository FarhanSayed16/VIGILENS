"""Sessions CRUD — JWT required."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.sessions import (
    SessionCreate,
    SessionListResponse,
    SessionRead,
    SessionSummary,
)
from app.services import session_service

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=SessionListResponse)
def list_sessions(
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
    room_config_id: Optional[int] = Query(default=None, gt=0),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> SessionListResponse:
    return session_service.list_sessions(
        db,
        room_config_id=room_config_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=SessionRead, status_code=201)
def create_session(
    body: SessionCreate,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> SessionRead:
    return session_service.create_session(db, body)


@router.get("/{session_id}", response_model=SessionRead)
def get_session(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> SessionRead:
    return session_service.get_session(db, session_id)


@router.get("/{session_id}/summary", response_model=SessionSummary)
def get_session_summary(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> SessionSummary:
    return session_service.get_summary(db, session_id)


@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> None:
    session_service.delete_session(db, session_id)
