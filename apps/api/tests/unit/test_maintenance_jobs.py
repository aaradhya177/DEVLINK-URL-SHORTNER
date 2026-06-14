from types import SimpleNamespace

from scripts import maintenance_jobs


class FakeSession:
    """Minimal async session for expiration job side-effect tests."""

    def __init__(self) -> None:
        self.committed = False
        self.executed = False

    async def execute(self, *_: object, **__: object) -> list[object]:
        self.executed = True
        return [
            SimpleNamespace(short_code="expired-a"),
            SimpleNamespace(short_code="expired-b"),
        ]

    async def commit(self) -> None:
        self.committed = True


class FakeSessionContext:
    """Async context manager returning a fake session."""

    def __init__(self, session: FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> FakeSession:
        return self.session

    async def __aexit__(self, *_: object) -> None:
        return None


async def test_expire_links_commits_and_invalidates_caches(monkeypatch) -> None:
    """Expired-link maintenance should invalidate every affected short-code cache."""
    session = FakeSession()
    invalidated: list[str] = []

    def session_factory() -> FakeSessionContext:
        return FakeSessionContext(session)

    async def invalidate_link_cache(short_code: str) -> None:
        invalidated.append(short_code)

    monkeypatch.setattr(maintenance_jobs, "async_session_factory", session_factory)
    monkeypatch.setattr(maintenance_jobs, "invalidate_link_cache", invalidate_link_cache)

    count = await maintenance_jobs.expire_links(limit=2)

    assert count == 2
    assert session.executed is True
    assert session.committed is True
    assert invalidated == ["expired-a", "expired-b"]
