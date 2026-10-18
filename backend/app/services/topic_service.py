"""Topic markers and active-topic resolution (for pulse later)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import Session as SessionModel
from app.db.models import Topic
from app.schemas.topics import TopicCreate, TopicListResponse, TopicRead


def _ensure_session(db: Session, session_id: int) -> SessionModel:
    row = db.get(SessionModel, session_id)
    if row is None:
        raise NotFoundError(f"Session {session_id} not found")
    return row


def elapsed_sec_for_session(session: SessionModel, now: Optional[datetime] = None) -> float:
    """Seconds since session clock start (started_at, else created_at)."""
    now = now or datetime.now(timezone.utc)
    start = session.started_at or session.created_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return max(0.0, (now - start).total_seconds())


def _to_read(row: Topic) -> TopicRead:
    return TopicRead(
        id=row.id,
        session_id=row.session_id,
        start_sec=row.start_sec,
        end_sec=row.end_sec,
        label=row.label,
    )


def list_topics(db: Session, session_id: int) -> TopicListResponse:
    _ensure_session(db, session_id)
    rows = db.scalars(
        select(Topic)
        .where(Topic.session_id == session_id)
        .order_by(Topic.start_sec.asc(), Topic.id.asc())
    ).all()
    return TopicListResponse(items=[_to_read(r) for r in rows], total=len(rows))


def create_topic(db: Session, session_id: int, payload: TopicCreate) -> TopicRead:
    session = _ensure_session(db, session_id)

    # Start lecture clock on first marker if not set
    if session.started_at is None:
        session.started_at = datetime.now(timezone.utc)

    start_sec = (
        float(payload.start_sec)
        if payload.start_sec is not None
        else elapsed_sec_for_session(session)
    )

    # Close previous open topic at this boundary
    open_topics: List[Topic] = list(
        db.scalars(
            select(Topic)
            .where(Topic.session_id == session_id, Topic.end_sec.is_(None))
            .order_by(Topic.start_sec.desc())
        ).all()
    )
    for prev in open_topics:
        if prev.start_sec <= start_sec:
            prev.end_sec = start_sec

    row = Topic(
        session_id=session_id,
        start_sec=start_sec,
        end_sec=payload.end_sec,
        label=payload.label,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_read(row)


def resolve_active_topic_at(
    db: Session, session_id: int, t_sec: float
) -> Optional[Topic]:
    """
    Active topic at time T: latest topic with start_sec <= T
    whose end_sec is null or >= T.
    """
    _ensure_session(db, session_id)
    rows = db.scalars(
        select(Topic)
        .where(Topic.session_id == session_id, Topic.start_sec <= t_sec)
        .order_by(Topic.start_sec.desc(), Topic.id.desc())
    ).all()
    for topic in rows:
        if topic.end_sec is None or topic.end_sec >= t_sec:
            return topic
    return None


def resolve_active_topic_id_at(
    db: Session, session_id: int, t_sec: float
) -> Optional[int]:
    topic = resolve_active_topic_at(db, session_id, t_sec)
    return topic.id if topic else None
