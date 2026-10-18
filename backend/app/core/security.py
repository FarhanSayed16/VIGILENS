"""Password check and JWT create/decode."""

from __future__ import annotations

import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.core.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def _looks_like_bcrypt(value: str) -> bool:
    return value.startswith(("$2a$", "$2b$", "$2y$"))


def verify_lecturer_password(plain: str, settings: Optional[Settings] = None) -> bool:
    """
    Verify lecturer password.

    Supports bcrypt hashes in LECTURER_PASSWORD (prefix $2b$ / $2a$ / $2y$).
    Plaintext env values still work for local MVP (constant-time compare).
    """
    settings = settings or get_settings()
    stored = settings.lecturer_password
    if _looks_like_bcrypt(stored):
        try:
            from passlib.context import CryptContext

            ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
            return bool(ctx.verify(plain, stored))
        except Exception as exc:  # noqa: BLE001
            logger.warning("bcrypt verify failed: %s", type(exc).__name__)
            return False
    return hmac.compare_digest(
        plain.encode("utf-8"),
        stored.encode("utf-8"),
    )


def verify_lecturer_username(username: str, settings: Optional[Settings] = None) -> bool:
    settings = settings or get_settings()
    return hmac.compare_digest(
        username.strip().encode("utf-8"),
        settings.lecturer_username.encode("utf-8"),
    )


def create_access_token(
    *,
    subject: str,
    settings: Optional[Settings] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expire_minutes)
    payload: Dict[str, Any] = {
        "sub": subject,
        "role": "lecturer",
        "iat": int(now.timestamp()),
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Optional[Settings] = None) -> Dict[str, Any]:
    settings = settings or get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])


class TokenError(Exception):
    pass


def get_subject_from_token(token: str, settings: Optional[Settings] = None) -> str:
    try:
        payload = decode_access_token(token, settings)
        sub = payload.get("sub")
        if not sub or not isinstance(sub, str):
            raise TokenError("Invalid token subject")
        if payload.get("role") != "lecturer":
            raise TokenError("Invalid token role")
        return sub
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc
