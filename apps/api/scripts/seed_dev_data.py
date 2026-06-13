import asyncio
import hashlib
import os
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.dialects.postgresql import insert

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://devlink:devlink@localhost:5432/devlink"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("KAFKA_BROKERS", "localhost:9092")
os.environ.setdefault("JWT_SECRET", "change-me-in-local-env")

from src.db.session import async_session_factory  # noqa: E402
from src.models import (  # noqa: E402
    ClickEvent,
    Link,
    LinkAnalyticsDaily,
    User,
    Workspace,
    WorkspaceMember,
)


USERS = [
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "email": "ada@example.com",
        "password_hash": None,
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "email": "grace@example.com",
        "password_hash": None,
    },
]

WORKSPACE_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


async def seed() -> None:
    now = datetime.now(UTC)
    links = [
        {
            "id": 7_390_000_000_001,
            "workspace_id": WORKSPACE_ID,
            "owner_id": USERS[0]["id"],
            "short_code": "AdaDocs",
            "destination_url": "https://docs.python.org/3/",
            "long_url_hash": url_hash("https://docs.python.org/3/"),
            "title": "Python docs",
            "is_active": True,
            "expires_at": None,
        },
        {
            "id": 7_390_000_000_002,
            "workspace_id": WORKSPACE_ID,
            "owner_id": USERS[1]["id"],
            "short_code": "GraceDB",
            "destination_url": "https://www.postgresql.org/docs/current/",
            "long_url_hash": url_hash("https://www.postgresql.org/docs/current/"),
            "title": "PostgreSQL docs",
            "is_active": True,
            "expires_at": now + timedelta(days=30),
        },
    ]

    async with async_session_factory() as session:
        for user in USERS:
            stmt = insert(User).values(**user)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={"email": stmt.excluded.email},
            )
            await session.execute(stmt)

        workspace_stmt = insert(Workspace).values(
            id=WORKSPACE_ID,
            name="DEVLINK Demo",
            owner_id=USERS[0]["id"],
        )
        workspace_stmt = workspace_stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": workspace_stmt.excluded.name,
                "owner_id": workspace_stmt.excluded.owner_id,
            },
        )
        await session.execute(workspace_stmt)

        for user in USERS:
            member_stmt = insert(WorkspaceMember).values(
                workspace_id=WORKSPACE_ID,
                user_id=user["id"],
                role="owner" if user["id"] == USERS[0]["id"] else "editor",
            )
            member_stmt = member_stmt.on_conflict_do_update(
                constraint="uq_workspace_members_member",
                set_={"role": member_stmt.excluded.role},
            )
            await session.execute(member_stmt)

        for link in links:
            link_stmt = insert(Link).values(**link)
            link_stmt = link_stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "workspace_id": link_stmt.excluded.workspace_id,
                    "owner_id": link_stmt.excluded.owner_id,
                    "short_code": link_stmt.excluded.short_code,
                    "destination_url": link_stmt.excluded.destination_url,
                    "long_url_hash": link_stmt.excluded.long_url_hash,
                    "title": link_stmt.excluded.title,
                    "is_active": link_stmt.excluded.is_active,
                    "expires_at": link_stmt.excluded.expires_at,
                },
            )
            await session.execute(link_stmt)

        click_events = [
            ClickEvent(
                link_id=links[0]["id"],
                clicked_at=now - timedelta(minutes=15),
                ip_hash=url_hash("127.0.0.1"),
                user_agent="Mozilla/5.0 DEVLINK seed",
                referer="https://example.com/newsletter",
                country="US",
                region="CA",
                city="San Francisco",
                device_type="desktop",
                browser="Firefox",
                os="Windows",
                metadata_json={"seeded": True},
            ),
            ClickEvent(
                link_id=links[0]["id"],
                clicked_at=now - timedelta(minutes=7),
                ip_hash=url_hash("127.0.0.2"),
                user_agent="Mozilla/5.0 DEVLINK seed",
                referer="https://example.com/blog",
                country="US",
                region="NY",
                city="New York",
                device_type="mobile",
                browser="Chrome",
                os="Android",
                metadata_json={"seeded": True},
            ),
            ClickEvent(
                link_id=links[1]["id"],
                clicked_at=now - timedelta(minutes=3),
                ip_hash=url_hash("127.0.0.3"),
                user_agent="Mozilla/5.0 DEVLINK seed",
                referer=None,
                country="IN",
                region="KA",
                city="Bengaluru",
                device_type="desktop",
                browser="Chrome",
                os="Windows",
                metadata_json={"seeded": True},
            ),
        ]
        session.add_all(click_events)

        analytics_rows = [
            {
                "link_id": links[0]["id"],
                "stat_date": now.date(),
                "country": "US",
                "device_type": "desktop",
                "referer_domain": "example.com",
                "click_count": 1,
            },
            {
                "link_id": links[0]["id"],
                "stat_date": now.date(),
                "country": "US",
                "device_type": "mobile",
                "referer_domain": "example.com",
                "click_count": 1,
            },
            {
                "link_id": links[1]["id"],
                "stat_date": now.date(),
                "country": "IN",
                "device_type": "desktop",
                "referer_domain": "",
                "click_count": 1,
            },
        ]
        for row in analytics_rows:
            analytics_stmt = insert(LinkAnalyticsDaily).values(**row)
            analytics_stmt = analytics_stmt.on_conflict_do_update(
                index_elements=[
                    "link_id",
                    "stat_date",
                    "country",
                    "device_type",
                    "referer_domain",
                ],
                set_={"click_count": analytics_stmt.excluded.click_count},
            )
            await session.execute(analytics_stmt)

        await session.commit()

    print("Seeded DEVLINK sample users, workspace, links, clicks, and daily analytics.")


if __name__ == "__main__":
    asyncio.run(seed())
