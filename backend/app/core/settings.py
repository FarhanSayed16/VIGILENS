"""Application settings loaded from environment / .env."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = vigilens/ (parent of backend/)
REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(REPO_ROOT / ".env"),
            str(BACKEND_ROOT / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://vigilens:change_me@localhost:5432/vigilens",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Security
    secret_key: str = Field(default="dev_only_change_me", alias="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=480, alias="JWT_EXPIRE_MINUTES")
    lecturer_username: str = Field(default="lecturer", alias="LECTURER_USERNAME")
    lecturer_password: str = Field(default="change_me", alias="LECTURER_PASSWORD")

    # Uploads
    upload_dir: str = Field(default=str(REPO_ROOT / "uploads"), alias="UPLOAD_DIR")
    max_upload_mb: int = Field(default=2048, alias="MAX_UPLOAD_MB")

    # CORS — comma-separated in env
    cors_origins: str = Field(
        default="http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    # Shared vision config
    config_path: str = Field(
        default=str(REPO_ROOT / "configs" / "default.yaml"),
        alias="CONFIG_PATH",
    )

    # Analysis worker: false = real YOLO/MediaPipe (Phase 20); true = synthetic (CI / Checkpoint A)
    use_fake_worker: bool = Field(default=False, alias="USE_FAKE_WORKER")

    # Optional cap on sampled frames for real worker (dev/smoke); None = full clip
    worker_max_frames: Optional[int] = Field(default=None, alias="WORKER_MAX_FRAMES")

    app_name: str = "VIGILENS API"
    app_version: str = "0.1.0"
    debug: bool = False

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("upload_dir", mode="before")
    @classmethod
    def resolve_upload_dir(cls, v: str) -> str:
        path = Path(v)
        if not path.is_absolute():
            path = (REPO_ROOT / path).resolve()
        return str(path)

    @field_validator("config_path", mode="before")
    @classmethod
    def resolve_config_path(cls, v: object) -> str:
        """Resolve CONFIG_PATH against repo root (not process CWD / backend/)."""
        if v is None or str(v).strip() == "":
            return str(REPO_ROOT / "configs" / "default.yaml")
        path = Path(str(v))
        if path.is_file():
            return str(path.resolve())
        if not path.is_absolute():
            return str((REPO_ROOT / path).resolve())
        return str(path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
