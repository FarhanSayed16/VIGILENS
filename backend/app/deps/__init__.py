"""FastAPI dependencies."""

from app.deps.auth import CurrentLecturer, get_current_lecturer
from app.deps.db import get_db

__all__ = ["CurrentLecturer", "get_current_lecturer", "get_db"]
