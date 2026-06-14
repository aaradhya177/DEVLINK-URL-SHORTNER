from datetime import UTC, datetime, timedelta

import pytest

from src.shared.cache import CachedLink


pytestmark = pytest.mark.integration


async def _register_login_create(client, payload: dict[str, object]) -> dict[str, object]:
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "redirect@example.com", "password": "correct-horse"},
    )
    assert register.status_code == 201
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "redirect@example.com", "password": "correct-horse"},
    )
    token = login.json()["access_token"]
    created = await client.post(
        "/api/v1/links",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 201
    return created.json()


@pytest.fixture()
def fake_redirect_cache(monkeypatch: pytest.MonkeyPatch) -> dict[str, CachedLink]:
    """Patch redirect cache functions with an in-memory cache."""
    cache: dict[str, CachedLink] = {}

    async def get_link_cache(short_code: str) -> CachedLink | None:
        return cache.get(short_code)

    async def set_link_cache(short_code: str, cached_link: CachedLink) -> None:
        cache[short_code] = cached_link

    async def increment_rate_limit(*_: object) -> tuple[bool, int]:
        return True, 119

    from src.redirect import service as redirect_service

    monkeypatch.setattr(redirect_service, "get_link_cache", get_link_cache)
    monkeypatch.setattr(redirect_service, "set_link_cache", set_link_cache)
    monkeypatch.setattr(redirect_service, "increment_rate_limit", increment_rate_limit)
    return cache


async def test_redirect_cache_miss_then_hit(api_client, fake_redirect_cache) -> None:
    """The first redirect should populate cache and the second should hit it."""
    link = await _register_login_create(
        api_client,
        {"destination_url": "https://example.com/target", "strip_tracking_params": True},
    )

    first = await api_client.get(f"/r/{link['short_code']}", follow_redirects=False)
    second = await api_client.get(f"/r/{link['short_code']}", follow_redirects=False)

    assert first.status_code == 307
    assert first.headers["location"] == "https://example.com/target"
    assert first.headers["X-Devlink-Cache"] == "MISS"
    assert second.headers["X-Devlink-Cache"] == "HIT"
    assert link["short_code"] in fake_redirect_cache


async def test_password_protected_redirect_flow(api_client, fake_redirect_cache) -> None:
    """Protected links should require password verification before redirect."""
    link = await _register_login_create(
        api_client,
        {
            "destination_url": "https://example.com/private",
            "password": "secret-pass",
            "strip_tracking_params": True,
        },
    )

    blocked = await api_client.get(f"/r/{link['short_code']}", follow_redirects=False)
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == {"requires_password": True}

    verified = await api_client.post(
        f"/r/{link['short_code']}/verify",
        json={"password": "secret-pass"},
    )
    assert verified.status_code == 200
    token = verified.json()["redirect_token"]

    redirected = await api_client.get(
        f"/r/{link['short_code']}?redirect_token={token}",
        follow_redirects=False,
    )
    assert redirected.status_code == 307


async def test_expired_and_flagged_redirect_pages(api_client, fake_redirect_cache) -> None:
    """Expired and flagged links should not collapse into generic 404 pages."""
    expired = await _register_login_create(
        api_client,
        {
            "destination_url": "https://example.com/expired",
            "expires_at": (datetime.now(UTC) + timedelta(seconds=10)).isoformat(),
            "strip_tracking_params": True,
        },
    )
    fake_redirect_cache[expired["short_code"]] = CachedLink(
        link_id=expired["id"],
        long_url=expired["destination_url"],
        expires_at=(datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
        is_active=True,
        is_password_protected=False,
        password_hash=None,
        workspace_id=None,
        flagged_reason=None,
    )

    expired_response = await api_client.get(
        f"/r/{expired['short_code']}",
        follow_redirects=False,
    )
    assert expired_response.status_code == 410
    assert "Expired link" in expired_response.text

    fake_redirect_cache[expired["short_code"]] = CachedLink(
        link_id=expired["id"],
        long_url=expired["destination_url"],
        expires_at=None,
        is_active=False,
        is_password_protected=False,
        password_hash=None,
        workspace_id=None,
        flagged_reason="google_safe_browsing_test_url",
    )
    flagged_response = await api_client.get(
        f"/r/{expired['short_code']}",
        follow_redirects=False,
    )
    assert flagged_response.status_code == 403
    assert "Blocked link" in flagged_response.text
