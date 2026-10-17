"""Lecturer authentication service."""

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    verify_lecturer_password,
    verify_lecturer_username,
)
from app.core.settings import Settings, get_settings
from app.schemas.auth import TokenResponse


def login_lecturer(username: str, password: str, settings: Settings | None = None) -> TokenResponse:
    settings = settings or get_settings()
    if not verify_lecturer_username(username, settings) or not verify_lecturer_password(
        password, settings
    ):
        raise UnauthorizedError("Invalid username or password")

    token = create_access_token(subject=settings.lecturer_username, settings=settings)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.jwt_expire_minutes,
        username=settings.lecturer_username,
    )
