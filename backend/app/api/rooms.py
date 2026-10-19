"""Rooms CRUD — JWT required."""

from typing import List

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.calibrate import (
    CalibrateDetectResponse,
    CalibrateSuggestBody,
    CalibrateSuggestResponse,
)
from app.schemas.rooms import RoomCreate, RoomRead, RoomUpdate
from app.services import calibrate_service, room_service

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=List[RoomRead])
def list_rooms(
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> List[RoomRead]:
    return room_service.list_rooms(db)


@router.post("", response_model=RoomRead, status_code=201)
def create_room(
    body: RoomCreate,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> RoomRead:
    return room_service.create_room(db, body)


@router.post("/calibrate/suggest", response_model=CalibrateSuggestResponse)
def calibrate_suggest(
    body: CalibrateSuggestBody,
    _lecturer: CurrentLecturer,
) -> CalibrateSuggestResponse:
    """Propose seat grid + board ROI from camera viewpoint (no image required)."""
    return calibrate_service.suggest_layout(body)


@router.post("/calibrate/detect", response_model=CalibrateDetectResponse)
async def calibrate_detect(
    _lecturer: CurrentLecturer,
    file: UploadFile = File(...),
    placement: str = Form("back_of_room"),
    rows: int = Form(3),
    cols: int = Form(4),
) -> CalibrateDetectResponse:
    """
    YOLO person boxes → seats when possible; always returns a target ROI
    for the chosen viewpoint. Falls back to seat grid if detect fails.
    """
    data = await file.read()
    if not data:
        from app.core.exceptions import AppError

        raise AppError("Empty upload", status_code=400, code="empty_upload")
    return calibrate_service.detect_from_bytes(
        data, placement=placement, rows=rows, cols=cols
    )


@router.get("/{room_id}", response_model=RoomRead)
def get_room(
    room_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> RoomRead:
    return room_service.get_room(db, room_id)


@router.put("/{room_id}", response_model=RoomRead)
def update_room(
    room_id: int,
    body: RoomUpdate,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> RoomRead:
    return room_service.update_room(db, room_id, body)
