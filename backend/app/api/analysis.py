"""Start analysis for a session — JWT required."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.jobs import AnalysisStartResponse
from app.services import job_service

router = APIRouter(prefix="/sessions/{session_id}", tags=["analysis"])


@router.post("/analysis", response_model=AnalysisStartResponse, status_code=202)
def start_analysis(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> AnalysisStartResponse:
    return job_service.start_analysis(db, session_id)
