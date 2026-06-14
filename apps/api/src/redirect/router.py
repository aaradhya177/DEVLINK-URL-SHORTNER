import uuid
from html import escape
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
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
) -> Response:
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
    except service.RedirectFlaggedError:
        return _blocked_page(short_code)
    except service.RedirectGoneError:
        return _expired_page(short_code)

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
    except service.RedirectFlaggedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
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


def _blocked_page(short_code: str) -> HTMLResponse:
    """Return a safety warning page for flagged short links."""
    return HTMLResponse(
        _status_page_html(
            "Blocked link",
            f"The short link {short_code} was disabled because it was flagged as unsafe.",
        ),
        status_code=status.HTTP_403_FORBIDDEN,
    )


def _expired_page(short_code: str) -> HTMLResponse:
    """Return an expiration page for inactive or expired short links."""
    return HTMLResponse(
        _status_page_html(
            "Expired link",
            f"The short link {short_code} is no longer active.",
        ),
        status_code=status.HTTP_410_GONE,
    )


def _status_page_html(title: str, message: str) -> str:
    """Build a tiny standalone redirect status page."""
    escaped_title = escape(title)
    escaped_message = escape(message)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: Inter, system-ui, sans-serif;
      color: #172033;
      background: #eef2f7;
    }}
    main {{
      width: min(92vw, 520px);
      padding: 28px;
      border: 1px solid #d7dee8;
      border-radius: 8px;
      background: #fff;
    }}
    h1 {{ margin: 0 0 10px; font-size: 1.5rem; }}
    p {{ margin: 0; color: #475569; line-height: 1.5; }}
  </style>
</head>
<body>
  <main>
    <h1>{escaped_title}</h1>
    <p>{escaped_message}</p>
  </main>
</body>
</html>"""
