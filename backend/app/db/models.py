"""
VIGILENS Postgres models — aggregates only.

Never store: face embeddings, face crops, student names, roll numbers,
student IDs, or permanent per-student histories.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.db.enums import JobStatus, SessionStatus, SourceType, TeachingMode

# JSONB on Postgres; plain JSON elsewhere (tests / fallback)
JsonType = JSON().with_variant(JSONB(), "postgresql")


class RoomConfig(Base):
    __tablename__ = "room_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    seat_regions_json: Mapped[Any] = mapped_column(JsonType, nullable=False, default=list)
    target_roi_json: Mapped[Optional[Any]] = mapped_column(JsonType, nullable=True)
    camera_defaults: Mapped[Optional[Any]] = mapped_column(JsonType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sessions: Mapped[list[Session]] = relationship(back_populates="room_config")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_config_id: Mapped[int] = mapped_column(
        ForeignKey("room_configs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    source_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SourceType.UPLOAD.value
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=SessionStatus.DRAFT.value, index=True
    )
    # Disk path under UPLOAD_DIR only — never permanent face assets
    video_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    # Optional second camera URL/index — display only; metrics use primary
    secondary_source_url: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
    )
    # Optional denormalized cache of latest teaching mode
    current_mode: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    room_config: Mapped[RoomConfig] = relationship(back_populates="sessions")
    topics: Mapped[list[Topic]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    mode_changes: Mapped[list[ModeChange]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    windows: Mapped[list[Window]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    events: Mapped[list[Event]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    pulse_responses: Mapped[list[PulseResponse]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    analysis_jobs: Mapped[list[AnalysisJob]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)

    session: Mapped[Session] = relationship(back_populates="topics")


class ModeChange(Base):
    __tablename__ = "mode_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    mode: Mapped[str] = mapped_column(
        String(32), nullable=False, default=TeachingMode.EXPLANATION.value
    )

    session: Mapped[Session] = relationship(back_populates="mode_changes")


class Window(Base):
    """30-second class-level aggregate — not per-face storage."""

    __tablename__ = "windows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    topic_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    teaching_mode: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    expected_regions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usable_regions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ttoi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ttoi_lo: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ttoi_hi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    head_down_cue_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hand_raise_events: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    candidate_decline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dominant_cue: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    data_quality_note: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # Per-seat orientation stats for heatmap (anonymous seat_id → O%)
    seat_stats_json: Mapped[Optional[Any]] = mapped_column(JsonType, nullable=True)

    session: Mapped[Session] = relationship(back_populates="windows")


class Event(Base):
    """Candidate orientation decline / group pattern — not 'attention dropped'."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_sec: Mapped[float] = mapped_column(Float, nullable=False)
    end_sec: Mapped[float] = mapped_column(Float, nullable=False)
    depth: Mapped[float] = mapped_column(Float, nullable=False)
    coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    topic_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    teaching_mode: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    dominant_cue: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kind: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, default="orientation_decline"
    )
    seat_ids_json: Mapped[Optional[Any]] = mapped_column(JsonType, nullable=True)
    group_label: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    lecturer_feedback: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    session: Mapped[Session] = relationship(back_populates="events")


class PulseResponse(Base):
    """Anonymous 1–5 pulse — no name, seat, or roll number."""

    __tablename__ = "pulse_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    score_1_to_5: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped[Session] = relationship(back_populates="pulse_responses")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=JobStatus.QUEUED.value, index=True
    )
    progress_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    session: Mapped[Session] = relationship(back_populates="analysis_jobs")
