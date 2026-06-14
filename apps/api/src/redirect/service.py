import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import verify_password
from src.links.repository import get_link_by_short_code
from src.shared.cache import (
    CachedLink,
    cached_link_from_model,
    get_link_cache,
    increment_rate_limit,
    set_link_cache,
)


logger = logging.getLogger(__name__)
REDIRECT_RATE_LIMIT = 120
REDIRECT_RATE_WINDOW_SECONDS = 60


class RedirectNotFoundError(Exception):
    """Raised when a short code does not exist."""


class RedirectGoneError(Exception):
    """Raised when a short code exists but cannot be redirected."""


class RedirectFlaggedError(Exception):
    """Raised when a short code is blocked by URL safety checks."""


class RedirectPasswordRequiredError(Exception):
    """Raised when a short code requires password verification."""


class RedirectInvalidPasswordError(Exception):
    """Raised when a redirect password is incorrect."""


class RedirectRateLimitedError(Exception):
    """Raised when a redirect exceeds hot-path abuse limits."""


@dataclass(frozen=True, slots=True)
class RedirectLookupTimings:
    """Milliseconds spent in redirect metadata lookup stages."""

    cache_lookup_ms: float
    db_fallback_ms: float


@dataclass(frozen=True, slots=True)
class RedirectMetadataResult:
    """Redirect metadata plus cache status and timing fields."""

    cached_link: CachedLink
    cache_status: str
    timings: RedirectLookupTimings


async def check_redirect_rate_limit(short_code: str, client_id: str) -> int:
    """Apply a Redis-backed fixed-window redirect rate limit."""
    key = f"rl:redirect:{short_code}:{hash_client_id(client_id)}"
    allowed, remaining = await increment_rate_limit(
        key,
        REDIRECT_RATE_LIMIT,
        REDIRECT_RATE_WINDOW_SECONDS,
    )
    if not allowed:
        raise RedirectRateLimitedError("Too many redirect requests.")
    return remaining


async def check_redirect_password_rate_limit(short_code: str, client_id: str) -> int:
    """Apply a stricter Redis-backed limit to redirect password attempts."""
    from app.core.config import settings

    key = f"rl:redirect-password:{short_code}:{hash_client_id(client_id)}"
    allowed, remaining = await increment_rate_limit(
        key,
        settings.redirect_password_attempt_limit,
        settings.redirect_password_attempt_window_seconds,
    )
    if not allowed:
        raise RedirectRateLimitedError("Too many password attempts.")
    return remaining


async def get_redirect_metadata(
    session: AsyncSession,
    short_code: str,
) -> tuple[CachedLink, str]:
    """Fetch redirect metadata from cache, falling back to the database."""
    result = await get_redirect_metadata_with_timings(session, short_code)
    return result.cached_link, result.cache_status


async def get_redirect_metadata_with_timings(
    session: AsyncSession,
    short_code: str,
) -> RedirectMetadataResult:
    """Fetch redirect metadata and return hot-path timing fields."""
    cache_start = perf_counter()
    cached_link = await get_link_cache(short_code)
    cache_lookup_ms = _elapsed_ms(cache_start)
    if cached_link is not None:
        _raise_if_unavailable(cached_link)
        return RedirectMetadataResult(
            cached_link=cached_link,
            cache_status="HIT",
            timings=RedirectLookupTimings(
                cache_lookup_ms=cache_lookup_ms,
                db_fallback_ms=0.0,
            ),
        )

    db_start = perf_counter()
    link = await get_link_by_short_code(session, short_code)
    db_fallback_ms = _elapsed_ms(db_start)
    if link is None:
        raise RedirectNotFoundError("Link not found.")

    cached_link = cached_link_from_model(link)
    _raise_if_unavailable(cached_link)
    await set_link_cache(short_code, cached_link)
    return RedirectMetadataResult(
        cached_link=cached_link,
        cache_status="MISS",
        timings=RedirectLookupTimings(
            cache_lookup_ms=cache_lookup_ms,
            db_fallback_ms=db_fallback_ms,
        ),
    )


async def verify_redirect_password(
    session: AsyncSession,
    short_code: str,
    password: str,
) -> None:
    """Verify a password-protected redirect password."""
    cached_link, _ = await get_redirect_metadata(session, short_code)
    if not cached_link.is_password_protected:
        return
    if cached_link.password_hash is None:
        raise RedirectPasswordRequiredError("Redirect password is required.")
    if not verify_password(password, cached_link.password_hash):
        raise RedirectInvalidPasswordError("Invalid redirect password.")


def log_click(
    short_code: str,
    link_id: int,
    cache_status: str,
    client_id: str,
    event_id: str,
    correlation_id: str | None = None,
) -> None:
    """Log a non-blocking click event placeholder for the future analytics phase."""
    logger.info(
        "redirect_click event_id=%s link_id=%s cache=%s",
        event_id,
        link_id,
        cache_status,
        extra={
            "event_id": event_id,
            "correlation_id": correlation_id,
            "link_id": link_id,
            "short_code": short_code,
            "cache": cache_status,
            "client_hash": hash_client_id(client_id),
        },
    )


def hash_client_id(client_id: str) -> str:
    """Hash a redirect client identifier before using it in logs or Redis keys."""
    return hashlib.sha256(client_id.encode("utf-8")).hexdigest()


def _elapsed_ms(start: float) -> float:
    """Return elapsed milliseconds from a perf_counter start."""
    return round((perf_counter() - start) * 1000, 3)


def _raise_if_unavailable(cached_link: CachedLink) -> None:
    """Raise when redirect metadata points to inactive or expired link."""
    if cached_link.flagged_reason is not None:
        raise RedirectFlaggedError("Link was blocked for safety.")

    if not cached_link.is_active:
        raise RedirectGoneError("Link is inactive.")

    if cached_link.expires_at is None:
        return

    expires_at = datetime.fromisoformat(cached_link.expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        raise RedirectGoneError("Link has expired.")
