"""Live cockpit: secondary source, seat stats, event group fields

Revision ID: 002_live_cockpit
Revises: 001_initial
Create Date: 2026-10-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_live_cockpit"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JsonType = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("secondary_source_url", sa.String(length=1024), nullable=True),
    )
    op.add_column("windows", sa.Column("seat_stats_json", JsonType, nullable=True))
    op.add_column(
        "events",
        sa.Column("kind", sa.String(length=64), nullable=True, server_default="orientation_decline"),
    )
    op.add_column("events", sa.Column("seat_ids_json", JsonType, nullable=True))
    op.add_column("events", sa.Column("group_label", sa.String(length=32), nullable=True))
    op.add_column(
        "events", sa.Column("lecturer_feedback", sa.String(length=32), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("events", "lecturer_feedback")
    op.drop_column("events", "group_label")
    op.drop_column("events", "seat_ids_json")
    op.drop_column("events", "kind")
    op.drop_column("windows", "seat_stats_json")
    op.drop_column("sessions", "secondary_source_url")
