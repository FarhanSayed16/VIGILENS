"""Session media: upload, source attach, video purge — JWT required."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.media import SourceUpdate, UploadResult
from app.schemas.sessions import SessionRead
from app.services import media_service

router = APIRouter(prefix="/sessions/{session_id}", tags=["media"])


@router.post("/upload", response_model=UploadResult)
async def upload_video(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
) -> UploadResult:
    result, _session = media_service.upload_video(
        db,
        session_id,
        filename=file.filename,
        content_type=file.content_type,
        fileobj=file.file,
    )
    return result


@router.put("/source", response_model=SessionRead)
def set_source(
    session_id: int,
    body: SourceUpdate,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> SessionRead:
    return media_service.set_source(db, session_id, body)


@router.delete("/video", response_model=SessionRead)
def purge_video(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> SessionRead:
    return media_service.purge_video(db, session_id)
