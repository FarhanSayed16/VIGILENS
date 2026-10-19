"""Controlled string values for MVP columns (documented enums)."""

from enum import StrEnum


class SourceType(StrEnum):
    UPLOAD = "upload"
    WEBCAM = "webcam"
    PHONE_RTSP = "phone_rtsp"


class SessionStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    ANALYZING = "analyzing"
    LIVE = "live"
    COMPLETE = "complete"
    ERROR = "error"
    PURGED_VIDEO = "purged_video"


class TeachingMode(StrEnum):
    EXPLANATION = "explanation"
    NOTE_TAKING = "note_taking"
    QA = "qa"
    DISCUSSION = "discussion"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


class DataQualityNote(StrEnum):
    INSUFFICIENT_COVERAGE = "insufficient_coverage"
    PARTIAL_WINDOW = "partial_window"
