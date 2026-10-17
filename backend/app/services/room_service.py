"""Room config CRUD and validation helpers."""

from __future__ import annotations

from typing import Any, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import RoomConfig
from app.schemas.rooms import CameraDefaults, RoomCreate, RoomRead, RoomUpdate, SeatRegion, TargetRoi


def _dump_region(region: SeatRegion | TargetRoi | dict | None) -> Any:
    if region is None:
        return None
    if hasattr(region, "model_dump"):
        return region.model_dump()
    return region


def _dump_seats(seats: List[SeatRegion] | List[dict]) -> list:
    out = []
    for s in seats:
        if hasattr(s, "model_dump"):
            out.append(s.model_dump())
        else:
            out.append(s)
    return out


def _to_read(room: RoomConfig) -> RoomRead:
    seats = room.seat_regions_json or []
    return RoomRead(
        id=room.id,
        name=room.name,
        seat_regions=seats,
        target_roi=room.target_roi_json,
        camera_defaults=room.camera_defaults,
        created_at=room.created_at,
        seat_count=len(seats) if isinstance(seats, list) else 0,
    )


def list_rooms(db: Session) -> List[RoomRead]:
    rows = db.scalars(select(RoomConfig).order_by(RoomConfig.id.desc())).all()
    return [_to_read(r) for r in rows]


def get_room(db: Session, room_id: int) -> RoomRead:
    room = db.get(RoomConfig, room_id)
    if room is None:
        raise NotFoundError(f"Room {room_id} not found")
    return _to_read(room)


def create_room(db: Session, payload: RoomCreate) -> RoomRead:
    cam = (
        payload.camera_defaults.model_dump()
        if payload.camera_defaults
        else CameraDefaults().model_dump()
    )
    room = RoomConfig(
        name=payload.name.strip(),
        seat_regions_json=_dump_seats(payload.seat_regions),
        target_roi_json=_dump_region(payload.target_roi),
        camera_defaults=cam,
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return _to_read(room)


def update_room(db: Session, room_id: int, payload: RoomUpdate) -> RoomRead:
    room = db.get(RoomConfig, room_id)
    if room is None:
        raise NotFoundError(f"Room {room_id} not found")

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        room.name = str(data["name"]).strip()
    if "seat_regions" in data and data["seat_regions"] is not None:
        room.seat_regions_json = data["seat_regions"]
    if "target_roi" in data:
        room.target_roi_json = data["target_roi"]
    if "camera_defaults" in data and data["camera_defaults"] is not None:
        room.camera_defaults = data["camera_defaults"]

    db.commit()
    db.refresh(room)
    return _to_read(room)
