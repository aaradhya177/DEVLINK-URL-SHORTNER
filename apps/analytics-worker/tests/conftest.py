import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://devlink:devlink@localhost:5432/devlink_test",
)
os.environ.setdefault("IP_HASH_SECRET", "local-dev-ip-hash-secret")


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Return the integration database URL or skip when not configured."""
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to run analytics-worker integration tests.")
    return database_url


@pytest.fixture(scope="session", autouse=True)
def migrated_database(test_database_url: str) -> Iterator[None]:
    """Apply API migrations because the worker writes to the shared schema."""
    os.environ["DATABASE_URL"] = test_database_url
    api_dir = Path(__file__).resolve().parents[2] / "api"
    config = Config(str(api_dir / "alembic.ini"))
    config.set_main_option("script_location", str(api_dir / "alembic"))
    command.upgrade(config, "head")
    yield


@pytest.fixture()
async def db_session(test_database_url: str) -> AsyncIterator[AsyncSession]:
    """Yield a clean migrated database session."""
    engine = create_async_engine(test_database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await _truncate(session)
        yield session
        await session.rollback()
        await _truncate(session)
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
