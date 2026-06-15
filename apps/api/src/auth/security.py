import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from src.db.session import get_session
from src.models.user import User


password_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return password_context.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verify a plaintext password against a stored hash."""
    if password_hash is None:
        return False
    return password_context.verify(password, password_hash)


def hash_refresh_token(refresh_token: str) -> str:
    """Hash a refresh token before storing or comparing it."""
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def create_access_token(user_id: uuid.UUID) -> tuple[str, datetime]:
    """Create a short-lived JWT access token for one user."""
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_minutes)
    token = _encode_jwt(
        {
            "sub": str(user_id),
            "type": "access",
            "exp": expires_at,
            "iat": datetime.now(UTC),
        }
    )
    return token, expires_at


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, uuid.UUID, datetime]:
    """Create a long-lived JWT refresh token with a unique token ID."""
    token_id = uuid.uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)
    token = _encode_jwt(
        {
            "sub": str(user_id),
            "jti": str(token_id),
            "type": "refresh",
            "exp": expires_at,
            "iat": datetime.now(UTC),
        }
    )
    return token, token_id, expires_at


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decode and validate a JWT, including its expected token type."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub", "type"]},
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("type") != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """FastAPI dependency returning the authenticated user."""
    payload = decode_token(token, expected_type="access")
    user_id_raw = payload.get("sub")
    try:
        user_id = uuid.UUID(str(user_id_raw))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def _encode_jwt(payload: dict[str, Any]) -> str:
    """Encode a JWT payload with configured API settings."""
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def secure_compare(value: str, expected: str) -> bool:
    """Compare secret-derived strings with constant-time comparison."""
    return hmac.compare_digest(value, expected)
