"""Retention helpers — honour privacy defaults from configs/default.yaml."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.services import media_service

logger = logging.getLogger(__name__)


def load_privacy_config() -> Dict[str, Any]:
    settings = get_settings()
    path = Path(settings.config_path)
    if not path.is_file():
        return {"purge_video_after_analysis": True}
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        privacy = data.get("privacy") or {}
        return {
            "purge_video_after_analysis": bool(
                privacy.get("purge_video_after_analysis", True)
            ),
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not read privacy config: %s", type(exc).__name__)
        return {"purge_video_after_analysis": True}


def maybe_purge_video_after_analysis(db: Session, session_id: int) -> bool:
    """
    If config says so, purge raw video after successful analysis.
    Aggregates (windows/events) are kept. Returns True if purge ran.
    """
    cfg = load_privacy_config()
    if not cfg.get("purge_video_after_analysis", True):
        return False
    try:
        media_service.purge_video(db, session_id)
        logger.info("Auto-purged video for session_id=%s after analysis", session_id)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Auto-purge after analysis failed session_id=%s: %s",
            session_id,
            type(exc).__name__,
        )
        return False
