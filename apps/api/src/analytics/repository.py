from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.link import Link
from src.models.link_analytics_daily import LinkAnalyticsDaily


async def get_total_clicks(session: AsyncSession, link_id: int) -> int:
    """Return denormalized total clicks for a link."""
    total = await session.scalar(select(Link.click_count).where(Link.id == link_id))
    return int(total or 0)


async def get_timeseries(
    session: AsyncSession,
    link_id: int,
    from_date: date,
    to_date: date,
) -> list[tuple[date, int]]:
    """Return daily clicks grouped by date from rollups."""
    stmt = (
        select(
            LinkAnalyticsDaily.stat_date,
            func.coalesce(func.sum(LinkAnalyticsDaily.click_count), 0),
        )
        .where(
            LinkAnalyticsDaily.link_id == link_id,
            LinkAnalyticsDaily.stat_date >= from_date,
            LinkAnalyticsDaily.stat_date <= to_date,
        )
        .group_by(LinkAnalyticsDaily.stat_date)
        .order_by(LinkAnalyticsDaily.stat_date.asc())
    )
    result = await session.execute(stmt)
    return [(row[0], int(row[1])) for row in result.all()]


async def get_geo_breakdown(
    session: AsyncSession,
    link_id: int,
) -> list[tuple[str, int]]:
    """Return clicks grouped by country from rollups."""
    stmt = (
        select(
            LinkAnalyticsDaily.country,
            func.coalesce(func.sum(LinkAnalyticsDaily.click_count), 0),
        )
        .where(LinkAnalyticsDaily.link_id == link_id)
        .group_by(LinkAnalyticsDaily.country)
        .order_by(func.sum(LinkAnalyticsDaily.click_count).desc())
    )
    result = await session.execute(stmt)
    return [(row[0] or "unknown", int(row[1])) for row in result.all()]


async def get_device_breakdown(
    session: AsyncSession,
    link_id: int,
) -> list[tuple[str, str, str, int]]:
    """Return clicks grouped by device, browser, and OS from rollups."""
    stmt = (
        select(
            LinkAnalyticsDaily.device_type,
            LinkAnalyticsDaily.browser,
            LinkAnalyticsDaily.os,
            func.coalesce(func.sum(LinkAnalyticsDaily.click_count), 0),
        )
        .where(LinkAnalyticsDaily.link_id == link_id)
        .group_by(
            LinkAnalyticsDaily.device_type,
            LinkAnalyticsDaily.browser,
            LinkAnalyticsDaily.os,
        )
        .order_by(func.sum(LinkAnalyticsDaily.click_count).desc())
    )
    result = await session.execute(stmt)
    return [
        (row[0] or "unknown", row[1] or "unknown", row[2] or "unknown", int(row[3]))
        for row in result.all()
    ]
