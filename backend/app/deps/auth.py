"""Auth dependencies for protected operator routes."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import UnauthorizedError
from app.core.security import TokenError, get_subject_from_token
from app.schemas.auth import LecturerMe

_bearer = HTTPBearer(auto_error=False)


def get_current_lecturer(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> LecturerMe:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Not authenticated")
    try:
        username = get_subject_from_token(credentials.credentials)
    except TokenError as exc:
        raise UnauthorizedError(str(exc)) from exc
    return LecturerMe(username=username, role="lecturer")


CurrentLecturer = Annotated[LecturerMe, Depends(get_current_lecturer)]
