"""Job status polling — JWT required."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.jobs import JobRead
from app.services import job_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> JobRead:
    return job_service.get_job(db, job_id)
