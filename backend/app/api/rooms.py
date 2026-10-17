"""Rooms CRUD — JWT required."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.rooms import RoomCreate, RoomRead, RoomUpdate
from app.services import room_service

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
