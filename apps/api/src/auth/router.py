from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import service
from src.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from src.db.session import get_session


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
    responses={
        401: {"description": "Invalid or expired credentials."},
        409: {"description": "The requested account already exists."},
        422: {"description": "Request validation failed."},
    },
)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
    description="Create a password-backed user account using a normalized email.",
)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Register a password-backed user."""
    try:
        user = await service.register(session, payload)
    except service.EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": str(user.id), "email": user.email}


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in",
    description="Verify password credentials and issue JWT access/refresh tokens.",
)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Exchange password credentials for access and refresh tokens."""
    try:
        return await service.login(session, payload)
    except service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh tokens",
    description=(
        "Rotate a refresh token and return a new access/refresh token pair. "
        "The previous refresh token is revoked."
    ),
)
async def refresh(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Rotate a refresh token and return a new token pair."""
    try:
        return await service.rotate_refresh_token(session, payload)
    except service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
    description="Revoke a refresh token so it can no longer be rotated.",
)
async def logout(
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Revoke a refresh token."""
    try:
        await service.logout(session, payload)
    except service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get(
    "/oauth/google",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Start Google OAuth",
    description="Placeholder endpoint for a future Google OAuth authorization flow.",
)
async def start_google_oauth() -> dict[str, str]:
    """Stub for beginning Google OAuth login."""
    return {
        "detail": (
            "Google OAuth is not configured yet. TODO: add client ID, client "
            "secret, redirect URI, state storage, and authorization redirect."
        )
    }


@router.get(
    "/oauth/google/callback",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Finish Google OAuth",
    description="Placeholder callback endpoint for a future Google OAuth flow.",
)
async def finish_google_oauth() -> dict[str, str]:
    """Stub for completing Google OAuth login."""
    return {
        "detail": (
            "Google OAuth callback is not implemented yet. TODO: validate state, "
            "exchange code for tokens, fetch profile, and upsert the user."
        )
    }
