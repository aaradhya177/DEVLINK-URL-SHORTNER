from datetime import UTC, datetime, timedelta
from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.redirect import service
from src.shared.cache import CachedLink


def _cached_link(
    *,
    is_active: bool = True,
    expires_at: str | None = None,
    flagged_reason: str | None = None,
) -> CachedLink:
    return CachedLink(
        link_id=1,
        long_url="https://example.com",
        expires_at=expires_at,
        is_active=is_active,
        is_password_protected=False,
        password_hash=None,
        workspace_id=None,
        flagged_reason=flagged_reason,
    )


def test_flagged_link_is_classified_before_inactive() -> None:
    """Safety-blocked redirects should render the blocked-link path."""
    with pytest.raises(service.RedirectFlaggedError):
        service._raise_if_unavailable(
            _cached_link(
                is_active=False,
                flagged_reason="google_safe_browsing_test_url",
            )
        )


def test_expired_link_is_gone() -> None:
    """Expired cached metadata should reject redirects."""
    expired = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()

    with pytest.raises(service.RedirectGoneError) as exc_info:
        service._raise_if_unavailable(_cached_link(expires_at=expired))

    assert str(exc_info.value) == "Link has expired."


def test_active_unexpired_link_is_available() -> None:
    """Valid cached metadata should pass without an exception."""
    future = (datetime.now(UTC) + timedelta(minutes=5)).isoformat()

    service._raise_if_unavailable(_cached_link(expires_at=future))


async def test_redirect_metadata_returns_cache_hit(monkeypatch) -> None:
    """Cached redirect metadata should avoid a database lookup."""
    cached = _cached_link()

    async def get_link_cache(short_code: str) -> CachedLink | None:
        assert short_code == "abc"
        return cached

    async def get_link_by_short_code(*_: object) -> object:
        raise AssertionError("database should not be queried on cache hit")

    monkeypatch.setattr(service, "get_link_cache", get_link_cache)
    monkeypatch.setattr(service, "get_link_by_short_code", get_link_by_short_code)

    result, cache_status = await service.get_redirect_metadata(object(), "abc")

    assert result is cached
    assert cache_status == "HIT"


async def test_redirect_metadata_db_miss_raises_not_found(monkeypatch) -> None:
    """Missing short codes should not be cached as successful redirects."""

    async def get_link_cache(_: str) -> None:
        return None

    async def get_link_by_short_code(*_: object) -> None:
        return None

    monkeypatch.setattr(service, "get_link_cache", get_link_cache)
    monkeypatch.setattr(service, "get_link_by_short_code", get_link_by_short_code)

    with pytest.raises(service.RedirectNotFoundError):
        await service.get_redirect_metadata(object(), "missing")


async def test_redirect_metadata_db_fallback_populates_cache(monkeypatch) -> None:
    """DB fallback should cache normalized redirect metadata."""
    cached_values: dict[str, CachedLink] = {}
    link = SimpleNamespace(
        id=7,
        destination_url="https://example.com",
        expires_at=None,
        is_active=True,
        password_hash=None,
        workspace_id=None,
        flagged_reason=None,
    )

    async def get_link_cache(_: str) -> None:
        return None

    async def get_link_by_short_code(_: object, short_code: str) -> object:
        assert short_code == "abc"
        return link

    async def set_link_cache(short_code: str, cached_link: CachedLink) -> None:
        cached_values[short_code] = cached_link

    monkeypatch.setattr(service, "get_link_cache", get_link_cache)
    monkeypatch.setattr(service, "get_link_by_short_code", get_link_by_short_code)
    monkeypatch.setattr(service, "set_link_cache", set_link_cache)

    result, cache_status = await service.get_redirect_metadata(object(), "abc")

    assert cache_status == "MISS"
    assert result.link_id == 7
    assert result.long_url == "https://example.com"
    assert cached_values["abc"] == result


async def test_redirect_password_verification(monkeypatch) -> None:
    """Protected links should use password verification and reject bad secrets."""
    protected = replace(
        _cached_link(is_active=True),
        is_password_protected=True,
        password_hash="hash",
    )

    async def get_redirect_metadata(*_: object) -> tuple[CachedLink, str]:
        return protected, "HIT"

    monkeypatch.setattr(service, "get_redirect_metadata", get_redirect_metadata)
    monkeypatch.setattr(service, "verify_password", lambda password, _: password == "ok")

    await service.verify_redirect_password(object(), "abc", "ok")
    with pytest.raises(service.RedirectInvalidPasswordError):
        await service.verify_redirect_password(object(), "abc", "bad")


async def test_redirect_rate_limit(monkeypatch) -> None:
    """Redirect limiter should surface retry errors and hash client identifiers."""
    calls: list[str] = []

    async def increment_rate_limit(
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        calls.append(key)
        assert limit == service.REDIRECT_RATE_LIMIT
        assert window_seconds == service.REDIRECT_RATE_WINDOW_SECONDS
        return False, 0

    monkeypatch.setattr(service, "increment_rate_limit", increment_rate_limit)

    with pytest.raises(service.RedirectRateLimitedError):
        await service.check_redirect_rate_limit("abc", "203.0.113.10")

    assert calls[0].startswith("rl:redirect:abc:")
    assert "203.0.113.10" not in calls[0]
