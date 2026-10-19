"""Start / poll / recover analysis for a session — JWT required."""

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.jobs import (
    AnalysisRecoverResponse,
    AnalysisStartResponse,
    JobRead,
)
from app.services import job_service

router = APIRouter(prefix="/sessions/{session_id}", tags=["analysis"])


@router.post("/analysis", response_model=AnalysisStartResponse, status_code=202)
def start_analysis(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> AnalysisStartResponse:
    return job_service.start_analysis(db, session_id)


@router.get("/analysis/latest", response_model=Optional[JobRead])
def latest_analysis_job(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> Optional[JobRead]:
    """Return latest job, or null when none exists (avoid 404 noise in the console)."""
    return job_service.get_latest_job(db, session_id)


@router.post("/analysis/recover", response_model=AnalysisRecoverResponse)
def recover_analysis(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> AnalysisRecoverResponse:
    """Clear orphan analyzing state when no live job owns the lock."""
    return job_service.recover_stuck_analysis(db, session_id)
