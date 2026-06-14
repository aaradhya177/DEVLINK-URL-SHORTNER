import os
from collections.abc import AsyncIterator, Iterator

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Return the integration database URL or skip when not configured."""
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run database integration tests.")
    return database_url


@pytest.fixture(scope="session", autouse=True)
def migrated_database(test_database_url: str) -> Iterator[None]:
    """Apply Alembic migrations once for the integration test session."""
    os.environ["DATABASE_URL"] = test_database_url
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    yield


@pytest.fixture()
async def db_session(test_database_url: str) -> AsyncIterator[AsyncSession]:
    """Yield a clean async session backed by the migrated test database."""
    engine = create_async_engine(test_database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await _truncate(session)
        yield session
        await session.rollback()
        await _truncate(session)
    await engine.dispose()


@pytest.fixture()
async def api_client(
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncIterator[AsyncClient]:
    """Return an HTTP client with DB and external services isolated."""
    engine = create_async_engine(test_database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    from app.main import app
    from src.db.session import get_session
    from src.links import service as links_service
    from src.redirect import router as redirect_router
    from src.shared import rate_limiter

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def no_rate_limit(*_: object, **__: object) -> None:
        return None

    async def no_safety_check(_: int) -> None:
        return None

    async def no_publish_click_event(*_: object, **__: object) -> None:
        return None

    monkeypatch.setattr(rate_limiter, "_check_sliding_window", no_rate_limit)
    monkeypatch.setattr(links_service, "check_link_safety_by_id", no_safety_check)
    monkeypatch.setattr(redirect_router, "publish_click_event", no_publish_click_event)
    app.dependency_overrides[get_session] = override_get_session
    await _truncate_with_factory(session_factory)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client

    app.dependency_overrides.clear()
    await _truncate_with_factory(session_factory)
    await engine.dispose()


async def _truncate(session: AsyncSession) -> None:
    """Clear database rows without dropping migrated schema."""
    await session.execute(
        text(
            """
            TRUNCATE TABLE
                link_analytics_daily,
                click_events,
                refresh_tokens,
                workspace_members,
                links,
                workspaces,
                users
            RESTART IDENTITY CASCADE
            """
        )
    )
    await session.commit()


async def _truncate_with_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Clear rows using a session factory."""
    async with session_factory() as session:
        await _truncate(session)
