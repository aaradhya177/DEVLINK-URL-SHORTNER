from datetime import UTC, datetime
import uuid

import pytest
from sqlalchemy import text

from worker.aggregator import process_click_event
from worker.events import ClickEventMessage


pytestmark = pytest.mark.integration


async def test_process_click_event_is_idempotent(db_session) -> None:
    """Duplicate event delivery should not double-count aggregates."""
    link_id = 44_000_001
    await db_session.execute(
        text(
            """
            INSERT INTO links (
                id, short_code, destination_url, long_url_hash, is_active
            )
            VALUES (
                :id, 'aggtest', 'https://example.com', repeat('a', 64), true
            )
            """
        ),
        {"id": link_id},
    )
    await db_session.commit()
    event = ClickEventMessage(
        event_id=uuid.uuid4(),
        link_id=link_id,
        timestamp=datetime.now(UTC),
        ip="203.0.113.42",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/125.0 Safari/537.36"
        ),
        referrer="https://ref.example/path?secret=value",
    )

    first_inserted, _ = await process_click_event(db_session, event)
    second_inserted, _ = await process_click_event(db_session, event)

    raw_count = await db_session.scalar(text("SELECT count(*) FROM click_events"))
    aggregate_clicks = await db_session.scalar(
        text(
            """
            SELECT COALESCE(sum(click_count), 0)
            FROM link_analytics_daily
            WHERE link_id = :link_id
            """
        ),
        {"link_id": link_id},
    )
    link_clicks = await db_session.scalar(
        text("SELECT click_count FROM links WHERE id = :link_id"),
        {"link_id": link_id},
    )
    stored_referrer = await db_session.scalar(text("SELECT referer FROM click_events"))
    stored_user_agent = await db_session.scalar(text("SELECT user_agent FROM click_events"))

    assert first_inserted is True
    assert second_inserted is False
    assert raw_count == 1
    assert aggregate_clicks == 1
    assert link_clicks == 1
    assert stored_referrer == "ref.example"
    assert stored_user_agent is None
