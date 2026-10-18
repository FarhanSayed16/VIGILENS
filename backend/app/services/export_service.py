"""CSV export of class-level aggregates only (no video paths, no PII)."""

from __future__ import annotations

import csv
import io

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.db.models import Event, Session as SessionModel, Topic, Window


def build_session_csv(db: Session, session_id: int) -> str:
    row = db.scalars(
        select(SessionModel)
        .options(joinedload(SessionModel.room_config))
        .where(SessionModel.id == session_id)
    ).unique().first()
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")

    topics = db.scalars(
        select(Topic)
        .where(Topic.session_id == session_id)
        .order_by(Topic.start_sec.asc(), Topic.id.asc())
    ).all()
    windows = db.scalars(
        select(Window)
        .where(Window.session_id == session_id)
        .order_by(Window.start_sec.asc(), Window.id.asc())
    ).all()
    events = db.scalars(
        select(Event)
        .where(Event.session_id == session_id)
        .order_by(Event.start_sec.asc(), Event.id.asc())
    ).all()

    buf = io.StringIO()
    w = csv.writer(buf)

    w.writerow(["# VIGILENS export — class-level aggregates only"])
    w.writerow(["# Excludes: raw video paths, face data, student identity, pulse PII (none stored)"])
    w.writerow([])
    w.writerow(["# SESSION"])
    w.writerow(["field", "value"])
    w.writerow(["session_id", row.id])
    w.writerow(["title", row.title])
    w.writerow(["status", row.status])
    w.writerow(["source_type", row.source_type])
    w.writerow(["room_name", row.room_config.name if row.room_config else ""])
    w.writerow(["room_config_id", row.room_config_id])
    w.writerow(["started_at", row.started_at.isoformat() if row.started_at else ""])
    w.writerow(["ended_at", row.ended_at.isoformat() if row.ended_at else ""])
    w.writerow(["created_at", row.created_at.isoformat() if row.created_at else ""])
    w.writerow(["has_video", bool(row.video_path)])
    w.writerow(["current_mode", row.current_mode or ""])

    w.writerow([])
    w.writerow(["# TOPICS"])
    w.writerow(["id", "start_sec", "end_sec", "label"])
    for t in topics:
        w.writerow([t.id, t.start_sec, t.end_sec if t.end_sec is not None else "", t.label])

    w.writerow([])
    w.writerow(["# WINDOWS"])
    w.writerow(
        [
            "id",
            "start_sec",
            "end_sec",
            "topic_id",
            "teaching_mode",
            "expected_regions",
            "usable_regions",
            "coverage_pct",
            "ttoi",
            "ttoi_lo",
            "ttoi_hi",
            "head_down_cue_pct",
            "hand_raise_events",
            "candidate_decline",
            "dominant_cue",
            "data_quality_note",
        ]
    )
    for win in windows:
        w.writerow(
            [
                win.id,
                win.start_sec,
                win.end_sec,
                win.topic_id if win.topic_id is not None else "",
                win.teaching_mode or "",
                win.expected_regions if win.expected_regions is not None else "",
                win.usable_regions if win.usable_regions is not None else "",
                win.coverage_pct if win.coverage_pct is not None else "",
                win.ttoi if win.ttoi is not None else "",
                win.ttoi_lo if win.ttoi_lo is not None else "",
                win.ttoi_hi if win.ttoi_hi is not None else "",
                win.head_down_cue_pct if win.head_down_cue_pct is not None else "",
                win.hand_raise_events if win.hand_raise_events is not None else "",
                win.candidate_decline,
                win.dominant_cue or "",
                win.data_quality_note or "",
            ]
        )

    w.writerow([])
    w.writerow(["# EVENTS (candidate orientation declines)"])
    w.writerow(
        [
            "id",
            "start_sec",
            "end_sec",
            "depth",
            "coverage_pct",
            "topic_id",
            "teaching_mode",
            "dominant_cue",
            "note",
        ]
    )
    for e in events:
        w.writerow(
            [
                e.id,
                e.start_sec,
                e.end_sec,
                e.depth,
                e.coverage_pct if e.coverage_pct is not None else "",
                e.topic_id if e.topic_id is not None else "",
                e.teaching_mode or "",
                e.dominant_cue or "",
                e.note or "",
            ]
        )

    return buf.getvalue()


def export_filename(session_id: int, title: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in title.strip())[:48]
    safe = safe or "session"
    return f"vigilens_{session_id}_{safe}.csv"
