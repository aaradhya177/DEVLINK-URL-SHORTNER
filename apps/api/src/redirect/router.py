from typing import Annotated
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.redirect import security, service
from src.redirect.schemas import PasswordVerifyRequest, PasswordVerifyResponse
from src.shared.kafka_producer import publish_click_event


router = APIRouter(prefix="/r", tags=["redirect"])


@router.get("/{short_code}")
async def redirect_short_code(
    short_code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
    redirect_token: str | None = None,
) -> RedirectResponse:
    """Resolve a short code and redirect when allowed."""
    client_id = _client_id(request)
    try:
        remaining = await service.check_redirect_rate_limit(short_code, client_id)
        cached_link, cache_status = await service.get_redirect_metadata(
            session,
            short_code,
        )
    except service.RedirectRateLimitedError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except service.RedirectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.RedirectGoneError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc

    cookie_token = request.cookies.get(security.redirect_cookie_name(short_code))
    if cached_link.is_password_protected:
        security.require_redirect_token(redirect_token or cookie_token, short_code)

    event_id = uuid.uuid4()
    service.log_click(
        short_code,
        cached_link.link_id,
        cache_status,
        client_id,
        str(event_id),
    )
    background_tasks.add_task(
        publish_click_event,
        cached_link.link_id,
        client_id,
        request.headers.get("user-agent"),
        request.headers.get("referer"),
        None,
        event_id,
    )
    response = RedirectResponse(
        cached_link.long_url,
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
    response.headers["X-Devlink-Cache"] = cache_status
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


@router.post("/{short_code}/verify", response_model=PasswordVerifyResponse)
async def verify_redirect_password(
    short_code: str,
    payload: PasswordVerifyRequest,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PasswordVerifyResponse:
    """Verify a protected redirect password and issue a short-lived token."""
    try:
        await service.verify_redirect_password(session, short_code, payload.password)
    except service.RedirectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.RedirectGoneError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc
    except service.RedirectInvalidPasswordError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    token, expires_at = security.create_redirect_token(short_code)
    expires_in = security.seconds_until(expires_at)
    response.set_cookie(
        key=security.redirect_cookie_name(short_code),
        value=token,
        max_age=expires_in,
        httponly=True,
        samesite="lax",
    )
    return PasswordVerifyResponse(redirect_token=token, expires_in=expires_in)


def _client_id(request: Request) -> str:
    """Return a stable-enough client identifier for redirect rate limiting."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is None:
        return "unknown"
    return request.client.host
