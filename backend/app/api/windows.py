"""Session window timeline — JWT required."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.results import WindowListResponse
from app.services import result_service

router = APIRouter(prefix="/sessions/{session_id}/windows", tags=["windows"])


@router.get("", response_model=WindowListResponse)
def list_windows(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
    min_coverage_pct: Optional[float] = Query(
        default=None,
        ge=0,
        le=100,
        description="Optional filter: only windows with coverage >= this %",
    ),
) -> WindowListResponse:
    return result_service.list_windows(
        db, session_id, min_coverage_pct=min_coverage_pct
    )
