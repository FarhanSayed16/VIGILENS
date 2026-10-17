"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI

from app.api.router import api_router
from app.core.cors import setup_cors
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    logger.info("VIGILENS API starting (v%s)", settings.app_version)
    logger.info("Upload dir: %s", upload_path)
    yield
    logger.info("VIGILENS API shutting down")


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "VIGILENS lecturer API — class-level TTOI timelines, "
            "coverage, and candidate orientation declines. "
            "Not an attention or emotion detector."
        ),
        lifespan=lifespan,
    )

    setup_cors(app, settings)
    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
