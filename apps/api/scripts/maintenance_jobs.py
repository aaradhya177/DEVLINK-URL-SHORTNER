import argparse
import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from src.db.session import async_session_factory
from src.shared.cache import invalidate_link_cache
from src.shared.url_safety import check_url_safety


async def expire_links(limit: int = 500) -> int:
    """Deactivate expired links and invalidate their redirect cache entries."""
    async with async_session_factory() as session:
        result = await session.execute(
            text(
                """
                WITH candidates AS (
                    SELECT id
                    FROM links
                    WHERE is_active = true
                      AND expires_at IS NOT NULL
                      AND expires_at < now()
                    ORDER BY expires_at
                    LIMIT :limit
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE links
                SET is_active = false,
                    updated_at = now()
                FROM candidates
                WHERE links.id = candidates.id
                RETURNING links.short_code
                """
            ),
            {"limit": limit},
        )
        short_codes = [row.short_code for row in result]
        await session.commit()

    for short_code in short_codes:
        await invalidate_link_cache(short_code)
    return len(short_codes)


async def recheck_pending_safety(
    limit: int = 100,
    lookback_minutes: int = 60,
) -> int:
    """Re-check recently created links whose initial safety check did not finish."""
    created_after = datetime.now(UTC) - timedelta(minutes=lookback_minutes)
    async with async_session_factory() as session:
        result = await session.execute(
            text(
                """
                WITH candidates AS (
                    SELECT id
                    FROM links
                    WHERE checked_at IS NULL
                      AND flagged_reason IS NULL
                      AND is_active = true
                      AND created_at >= :created_after
                    ORDER BY created_at
                    LIMIT :limit
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE links
                SET checked_at = now()
                FROM candidates
                WHERE links.id = candidates.id
                RETURNING links.id, links.destination_url, links.short_code
                """
            ),
            {"limit": limit, "created_after": created_after},
        )
        rows = result.mappings().all()
        await session.commit()

    processed = 0
    for row in rows:
        safety = await check_url_safety(row["destination_url"])
        async with async_session_factory() as session:
            if safety.is_malicious:
                await session.execute(
                    text(
                        """
                        UPDATE links
                        SET is_active = false,
                            flagged_reason = :flagged_reason,
                            checked_at = now(),
                            updated_at = now()
                        WHERE id = :link_id
                        """
                    ),
                    {
                        "link_id": row["id"],
                        "flagged_reason": safety.reason or "malicious_url",
                    },
                )
                await session.commit()
                await invalidate_link_cache(row["short_code"])
            elif safety.checked:
                await session.execute(
                    text("UPDATE links SET checked_at = now() WHERE id = :link_id"),
                    {"link_id": row["id"]},
                )
                await session.commit()
            else:
                # Fail open on provider timeout/failure; reset checked_at so cron can retry.
                await session.execute(
                    text("UPDATE links SET checked_at = NULL WHERE id = :link_id"),
                    {"link_id": row["id"]},
                )
                await session.commit()
        processed += 1
    return processed


async def run(command: str, limit: int, lookback_minutes: int) -> None:
    """Run one maintenance command."""
    if command == "expire-links":
        count = await expire_links(limit)
        print(f"expired_links={count}")
        return
    count = await recheck_pending_safety(limit, lookback_minutes)
    print(f"rechecked_links={count}")


def main() -> None:
    """CLI entrypoint for cron or lightweight schedulers."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["expire-links", "recheck-safety"])
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--lookback-minutes", type=int, default=60)
    args = parser.parse_args()
    asyncio.run(run(args.command, args.limit, args.lookback_minutes))


if __name__ == "__main__":
    main()
