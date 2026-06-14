import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.link import Link
from src.models.workspace_member import WorkspaceMember


async def create_link(session: AsyncSession, link: Link) -> Link:
    """Persist a new link and flush it so database defaults are available."""
    session.add(link)
    await session.flush()
    await session.refresh(link)
    return link


async def get_link_by_id(
    session: AsyncSession,
    link_id: int,
) -> Link | None:
    """Fetch one link by Snowflake ID."""
    return await session.get(Link, link_id)


async def get_link_by_short_code(
    session: AsyncSession,
    short_code: str,
) -> Link | None:
    """Fetch one link by short code for redirect and alias collision checks."""
    return await session.scalar(select(Link).where(Link.short_code == short_code))


async def get_link_by_long_url_hash(
    session: AsyncSession,
    long_url_hash: str,
    owner_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    now: datetime | None = None,
) -> Link | None:
    """Fetch an active existing link for deduplication."""
    stmt = select(Link).where(
        Link.long_url_hash == long_url_hash,
        Link.is_active.is_(True),
    )
    if owner_id is None:
        stmt = stmt.where(Link.owner_id.is_(None))
    else:
        stmt = stmt.where(Link.owner_id == owner_id)

    if workspace_id is None:
        stmt = stmt.where(Link.workspace_id.is_(None))
    else:
        stmt = stmt.where(Link.workspace_id == workspace_id)

    if now is not None:
        stmt = stmt.where(or_(Link.expires_at.is_(None), Link.expires_at > now))

    stmt = stmt.order_by(Link.created_at.desc())
    return await session.scalar(stmt)


async def get_links_by_long_url_hashes(
    session: AsyncSession,
    long_url_hashes: set[str],
    owner_id: uuid.UUID,
    workspace_id: uuid.UUID | None,
    now: datetime,
) -> Sequence[Link]:
    """Fetch active dedup candidates for a batch of URL hashes."""
    if not long_url_hashes:
        return []

    stmt = select(Link).where(
        Link.long_url_hash.in_(long_url_hashes),
        Link.owner_id == owner_id,
        Link.is_active.is_(True),
        or_(Link.expires_at.is_(None), Link.expires_at > now),
    )
    if workspace_id is None:
        stmt = stmt.where(Link.workspace_id.is_(None))
    else:
        stmt = stmt.where(Link.workspace_id == workspace_id)

    result = await session.scalars(stmt.order_by(Link.created_at.desc()))
    return result.all()


async def list_links(
    session: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    include_inactive: bool = False,
) -> Sequence[Link]:
    """List links a user owns or can access through workspace membership."""
    workspace_ids = select(WorkspaceMember.workspace_id).where(
        WorkspaceMember.user_id == user_id
    )
    stmt: Select[tuple[Link]] = select(Link).where(
        or_(Link.owner_id == user_id, Link.workspace_id.in_(workspace_ids))
    )
    if not include_inactive:
        stmt = stmt.where(Link.is_active.is_(True))

    stmt = stmt.order_by(Link.created_at.desc()).limit(limit).offset(offset)
    result = await session.scalars(stmt)
    return result.all()


async def update_link(session: AsyncSession, link: Link) -> Link:
    """Flush and refresh an updated link."""
    await session.flush()
    await session.refresh(link)
    return link


async def soft_delete_link(
    session: AsyncSession,
    link: Link,
    deleted_at: datetime,
) -> Link:
    """Deactivate a link while keeping it available for audit/history."""
    link.is_active = False
    link.updated_at = deleted_at
    await session.flush()
    await session.refresh(link)
    return link
