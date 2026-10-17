"""Initial MVP schema — room_configs through analysis_jobs

Revision ID: 001_initial
Revises:
Create Date: 2026-10-17

No PII / face / identity columns by design.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JsonType = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.create_table(
        "room_configs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "seat_regions_json",
            JsonType,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("target_roi_json", JsonType, nullable=True),
        sa.Column("camera_defaults", JsonType, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("room_config_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_type", sa.String(length=32), nullable=False, server_default="upload"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("video_path", sa.String(length=1024), nullable=True),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("current_mode", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["room_config_id"], ["room_configs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sessions_room_config_id", "sessions", ["room_config_id"])
    op.create_index("ix_sessions_status", "sessions", ["status"])

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("start_sec", sa.Float(), nullable=False),
        sa.Column("end_sec", sa.Float(), nullable=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_topics_session_id", "topics", ["session_id"])

    op.create_table(
        "mode_changes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("start_sec", sa.Float(), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False, server_default="explanation"),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mode_changes_session_id", "mode_changes", ["session_id"])

    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("progress_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analysis_jobs_session_id", "analysis_jobs", ["session_id"])
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])

    op.create_table(
        "windows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("start_sec", sa.Float(), nullable=False),
        sa.Column("end_sec", sa.Float(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("teaching_mode", sa.String(length=32), nullable=True),
        sa.Column("expected_regions", sa.Integer(), nullable=True),
        sa.Column("usable_regions", sa.Integer(), nullable=True),
        sa.Column("coverage_pct", sa.Float(), nullable=True),
        sa.Column("ttoi", sa.Float(), nullable=True),
        sa.Column("ttoi_lo", sa.Float(), nullable=True),
        sa.Column("ttoi_hi", sa.Float(), nullable=True),
        sa.Column("head_down_cue_pct", sa.Float(), nullable=True),
        sa.Column("hand_raise_events", sa.Integer(), nullable=True),
        sa.Column(
            "candidate_decline",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("dominant_cue", sa.String(length=64), nullable=True),
        sa.Column("data_quality_note", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_windows_session_id", "windows", ["session_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("start_sec", sa.Float(), nullable=False),
        sa.Column("end_sec", sa.Float(), nullable=False),
        sa.Column("depth", sa.Float(), nullable=False),
        sa.Column("coverage_pct", sa.Float(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("teaching_mode", sa.String(length=32), nullable=True),
        sa.Column("dominant_cue", sa.String(length=64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_session_id", "events", ["session_id"])

    op.create_table(
        "pulse_responses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("score_1_to_5", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pulse_responses_session_id", "pulse_responses", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_pulse_responses_session_id", table_name="pulse_responses")
    op.drop_table("pulse_responses")
    op.drop_index("ix_events_session_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_windows_session_id", table_name="windows")
    op.drop_table("windows")
    op.drop_index("ix_analysis_jobs_status", table_name="analysis_jobs")
    op.drop_index("ix_analysis_jobs_session_id", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
    op.drop_index("ix_mode_changes_session_id", table_name="mode_changes")
    op.drop_table("mode_changes")
    op.drop_index("ix_topics_session_id", table_name="topics")
    op.drop_table("topics")
    op.drop_index("ix_sessions_status", table_name="sessions")
    op.drop_index("ix_sessions_room_config_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_table("room_configs")
