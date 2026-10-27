"""Live lecture Start / Stop / state — JWT required."""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.live import EventFeedbackBody, LiveStartBody, LiveState, SecondarySourceBody
from app.services import live_service

router = APIRouter(prefix="/sessions/{session_id}/live", tags=["live"])


@router.get("/state", response_model=LiveState)
def live_state(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> LiveState:
    return live_service.get_live_state(db, session_id)


@router.get("/preview.jpg")
def live_preview(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> Response:
    """Worker camera frame with seat/person overlays (poll while live)."""
    jpeg = live_service.get_preview_jpeg(db, session_id)
    if not jpeg:
        # 204 — no body; clients treat as “not ready” without 404 noise
        return Response(status_code=204, headers={"Cache-Control": "no-store"})
    return Response(
        content=jpeg,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@router.post("/camera", status_code=204)
async def live_camera_frame(
    session_id: int,
    request: Request,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> Response:
    """JPEG from the phone browser camera. The worker reads the latest frame."""
    body = await request.body()
    if len(body) < 32 or len(body) > 2_500_000 or not body.startswith(b"\xff\xd8"):
        raise AppError(
            "Expected a JPEG frame from the phone camera",
            status_code=400,
            code="bad_camera_frame",
        )
    live_service.ingest_phone_frame(db, session_id, body)
    return Response(status_code=204)


@router.post("/start", response_model=LiveState)
def live_start(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
    body: Optional[LiveStartBody] = None,
) -> LiveState:
    return live_service.start_live(
        db,
        session_id,
        browser_camera=bool(body and body.browser_camera),
    )


@router.post("/stop", response_model=LiveState)
def live_stop(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> LiveState:
    return live_service.stop_live(db, session_id)


@router.put("/secondary", response_model=LiveState)
def set_secondary(
    session_id: int,
    body: SecondarySourceBody,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> LiveState:
    return live_service.set_secondary_source(
        db, session_id, body.secondary_source_url
    )


@router.post("/events/{event_id}/feedback")
def event_feedback(
    session_id: int,
    event_id: int,
    body: EventFeedbackBody,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> dict:
    return live_service.set_event_feedback(
        db, session_id, event_id, body.feedback
    )
