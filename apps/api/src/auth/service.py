import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from src.auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from src.models.refresh_token import RefreshToken
from src.models.user import User


class AuthServiceError(Exception):
    """Base class for authentication service errors."""


class EmailAlreadyRegisteredError(AuthServiceError):
    """Raised when a registration email already exists."""


class InvalidCredentialsError(AuthServiceError):
    """Raised when credentials or refresh tokens are invalid."""


async def register(session: AsyncSession, payload: RegisterRequest) -> User:
    """Create a new user with a hashed password."""
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise EmailAlreadyRegisteredError("Email is already registered.") from exc

    await session.refresh(user)
    return user


async def login(session: AsyncSession, payload: LoginRequest) -> TokenResponse:
    """Verify password credentials and issue access and refresh tokens."""
    user = await _get_user_by_email(session, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password.")
    return await _issue_token_pair(session, user)


async def rotate_refresh_token(
    session: AsyncSession,
    payload: RefreshRequest,
) -> TokenResponse:
    """Rotate a valid refresh token and revoke the previous token."""
    token_record = await _get_valid_refresh_token(session, payload.refresh_token)
    user = await session.get(User, token_record.user_id)
    if user is None:
        raise InvalidCredentialsError("Invalid refresh token.")

    access_token, access_expires_at = create_access_token(user.id)
    refresh_token, refresh_token_id, refresh_expires_at = create_refresh_token(user.id)
    replacement = RefreshToken(
        id=refresh_token_id,
        user_id=user.id,
        token_hash=hash_refresh_token(refresh_token),
        expires_at=refresh_expires_at,
    )
    token_record.revoked_at = datetime.now(UTC)
    token_record.replaced_by_token_id = refresh_token_id
    session.add(replacement)
    await session.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=_seconds_until(access_expires_at),
    )


async def logout(session: AsyncSession, payload: RefreshRequest) -> None:
    """Revoke a refresh token if it is currently valid."""
    token_record = await _get_valid_refresh_token(session, payload.refresh_token)
    token_record.revoked_at = datetime.now(UTC)
    await session.commit()


async def _issue_token_pair(session: AsyncSession, user: User) -> TokenResponse:
    """Create and persist a refresh token, returning both bearer tokens."""
    access_token, access_expires_at = create_access_token(user.id)
    refresh_token, refresh_token_id, refresh_expires_at = create_refresh_token(user.id)
    session.add(
        RefreshToken(
            id=refresh_token_id,
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=refresh_expires_at,
        )
    )
    await session.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=_seconds_until(access_expires_at),
    )


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Fetch a user by case-normalized email."""
    stmt = select(User).where(func.lower(User.email) == email.lower())
    return await session.scalar(stmt)


async def _get_valid_refresh_token(
    session: AsyncSession,
    refresh_token: str,
) -> RefreshToken:
    """Validate a refresh token and return its database record."""
    try:
        from src.auth.security import decode_token

        payload = decode_token(refresh_token, expected_type="refresh")
        token_id = uuid.UUID(str(payload.get("jti")))
    except (HTTPException, ValueError) as exc:
        if isinstance(exc, HTTPException):
            raise InvalidCredentialsError("Invalid refresh token.") from exc
        raise InvalidCredentialsError("Invalid refresh token.") from exc

    token_record = await session.get(RefreshToken, token_id)
    now = datetime.now(UTC)
    if (
        token_record is None
        or token_record.revoked_at is not None
        or token_record.expires_at <= now
        or token_record.token_hash != hash_refresh_token(refresh_token)
    ):
        raise InvalidCredentialsError("Invalid refresh token.")
    return token_record


def _seconds_until(expires_at: datetime) -> int:
    """Return whole seconds until an expiration timestamp."""
    return max(0, int((expires_at - datetime.now(UTC)).total_seconds()))
