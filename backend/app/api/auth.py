"""Auth routes — login (public) and me (JWT)."""

from fastapi import APIRouter

from app.core.settings import get_settings
from app.deps.auth import CurrentLecturer
from app.schemas.auth import LecturerMe, LoginRequest, TokenResponse
from app.services.auth_service import login_lecturer

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    """Issue lecturer JWT. Credentials from env (LECTURER_USERNAME / LECTURER_PASSWORD)."""
    return login_lecturer(body.username, body.password)


@router.get("/me", response_model=LecturerMe)
def me(lecturer: CurrentLecturer) -> LecturerMe:
    """Protected operator route — proves JWT works."""
    return lecturer


@router.get("/public-info")
def public_info() -> dict:
    """Tiny public hint (no secrets / no username) for frontend wiring checks."""
    settings = get_settings()
    return {
        "auth": "jwt",
        "token_minutes": settings.jwt_expire_minutes,
        "use_fake_worker": bool(settings.use_fake_worker),
    }
