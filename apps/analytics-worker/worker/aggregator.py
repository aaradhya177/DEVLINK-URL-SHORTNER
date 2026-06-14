import hashlib
from datetime import UTC, datetime
from time import perf_counter
from urllib.parse import urlsplit

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from worker.config import settings
from worker.events import ClickEventMessage
from worker.geo_resolver import GeoResolver
from worker.ua_parser import parse_user_agent


geo_resolver = GeoResolver()


async def process_click_event(
    session: AsyncSession,
    event: ClickEventMessage,
) -> tuple[bool, float]:
    """Persist one click event and update aggregates idempotently."""
    start = perf_counter()
    clicked_at = _as_utc(event.timestamp)
    geo = geo_resolver.resolve(event.ip)
    ua = parse_user_agent(event.user_agent)
    referrer_domain = _referrer_domain(event.referrer)
    ip_hash = _hash_ip(event.ip, clicked_at)
    insert_result = await session.execute(
        text(
            """
            INSERT INTO click_events (
                id, clicked_at, link_id, ip_hash, user_agent, referer,
                country, region, city, device_type, browser, os, metadata_json
            )
            VALUES (
                :id, :clicked_at, :link_id, :ip_hash, :user_agent, :referer,
                :country, :region, :city, :device_type, :browser, :os,
                :metadata_json
            )
            ON CONFLICT (id, clicked_at) DO NOTHING
            """
        ).bindparams(bindparam("metadata_json", type_=JSONB)),
        {
            "id": event.event_id,
            "clicked_at": clicked_at,
            "link_id": event.link_id,
            "ip_hash": ip_hash,
            "user_agent": None,
            "referer": referrer_domain,
            "country": geo["country"],
            "region": geo["region"],
            "city": geo["city"],
            "device_type": ua["device_type"],
            "browser": ua["browser"],
            "os": ua["os"],
            "metadata_json": {"event_id": str(event.event_id)},
        },
    )

    inserted = insert_result.rowcount == 1
    if inserted:
        await _increment_aggregates(session, event, clicked_at, geo, ua, referrer_domain)

    await session.commit()
    return inserted, (perf_counter() - start) * 1000


async def _increment_aggregates(
    session: AsyncSession,
    event: ClickEventMessage,
    clicked_at: datetime,
    geo: dict[str, str | None],
    ua: dict[str, str | None],
    referrer_domain: str,
) -> None:
    """Increment daily and denormalized link aggregates."""
    await session.execute(
        text(
            """
            INSERT INTO link_analytics_daily (
                link_id, stat_date, country, device_type, referer_domain,
                click_count
            )
            VALUES (
                :link_id, :stat_date, :country, :device_type,
                :referer_domain, 1
            )
            ON CONFLICT (
                link_id, stat_date, country, device_type, referer_domain
            )
            DO UPDATE SET
                click_count = link_analytics_daily.click_count + 1,
                updated_at = now()
            """
        ),
        {
            "link_id": event.link_id,
            "stat_date": clicked_at.date(),
            "country": geo["country"] or "",
            "device_type": ua["device_type"] or "",
            "referer_domain": referrer_domain,
        },
    )
    await session.execute(
        text("UPDATE links SET click_count = click_count + 1 WHERE id = :link_id"),
        {"link_id": event.link_id},
    )


def _hash_ip(ip_address: str, clicked_at: datetime) -> str:
    """Hash an IP with a daily salt; never persist the raw address."""
    salt = f"{settings.ip_hash_secret}:{clicked_at.date().isoformat()}"
    return hashlib.sha256(f"{salt}:{ip_address}".encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _referrer_domain(referrer: str | None) -> str:
    """Return only the referrer domain, dropping path/query PII."""
    if not referrer:
        return ""
    return (urlsplit(referrer).hostname or "").lower()
