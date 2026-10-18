"""CSV export of session aggregates — JWT required."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.services import export_service, session_service

router = APIRouter(prefix="/sessions/{session_id}", tags=["export"])


@router.get("/export")
def export_session_csv(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> Response:
    session = session_service.get_session(db, session_id)
    csv_text = export_service.build_session_csv(db, session_id)
    filename = export_service.export_filename(session_id, session.title)
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
