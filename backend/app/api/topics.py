"""Topic markers nested under sessions — JWT required."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps.auth import CurrentLecturer
from app.deps.db import get_db
from app.schemas.topics import TopicCreate, TopicListResponse, TopicRead
from app.services import topic_service

router = APIRouter(prefix="/sessions/{session_id}/topics", tags=["topics"])


@router.get("", response_model=TopicListResponse)
def list_topics(
    session_id: int,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> TopicListResponse:
    return topic_service.list_topics(db, session_id)


@router.post("", response_model=TopicRead, status_code=201)
def create_topic(
    session_id: int,
    body: TopicCreate,
    _lecturer: CurrentLecturer,
    db: Session = Depends(get_db),
) -> TopicRead:
    return topic_service.create_topic(db, session_id, body)
