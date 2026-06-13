from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError

from app.core.config import settings


REDIRECT_TOKEN_MINUTES = 5


def create_redirect_token(short_code: str) -> tuple[str, datetime]:
    """Create a short-lived JWT allowing redirect for one protected link."""
    expires_at = datetime.now(UTC) + timedelta(minutes=REDIRECT_TOKEN_MINUTES)
    token = jwt.encode(
        {
            "short_code": short_code,
            "type": "redirect",
            "exp": expires_at,
            "iat": datetime.now(UTC),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_at


def verify_redirect_token(token: str | None, short_code: str) -> bool:
    """Return whether a redirect token is valid for short_code."""
    if token is None:
        return False

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "type", "short_code"]},
        )
    except InvalidTokenError:
        return False

    return payload.get("type") == "redirect" and payload.get("short_code") == short_code


def require_redirect_token(token: str | None, short_code: str) -> None:
    """Raise 403 when the redirect token is missing or invalid."""
    if not verify_redirect_token(token, short_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"requires_password": True},
        )


def seconds_until(expires_at: datetime) -> int:
    """Return whole seconds until a token expiration timestamp."""
    return max(0, int((expires_at - datetime.now(UTC)).total_seconds()))


def redirect_cookie_name(short_code: str) -> str:
    """Return the cookie name used for protected redirect access."""
    safe_code = "".join(char if char.isalnum() else "_" for char in short_code)
    return f"devlink_redirect_{safe_code}"
