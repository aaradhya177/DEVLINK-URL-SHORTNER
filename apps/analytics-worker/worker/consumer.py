import json
import logging

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from worker.aggregator import process_click_event
from worker.config import settings
from worker.db import async_session_factory
from worker.events import ClickEventMessage


logger = logging.getLogger(__name__)


async def consume_click_events() -> None:
    """Consume click events forever and write analytics records."""
    consumer = AIOKafkaConsumer(
        settings.click_events_topic,
        bootstrap_servers=settings.kafka_brokers,
        group_id=settings.kafka_group_id,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    logger.info("analytics_consumer_started")
    try:
        async for message in consumer:
            await _handle_message(consumer, message)
    finally:
        await consumer.stop()


async def _handle_message(consumer: AIOKafkaConsumer, message: object) -> None:
    """Process one Kafka message and commit its offset when handled."""
    event: ClickEventMessage | None = None
    try:
        payload = json.loads(message.value.decode("utf-8"))
        event = ClickEventMessage.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
        logger.warning(
            "malformed_click_event_skipped",
            extra={"error": type(exc).__name__},
        )
        await consumer.commit()
        return

    try:
        async with async_session_factory() as session:
            inserted, processing_ms = await process_click_event(session, event)
    except SQLAlchemyError as exc:
        logger.exception(
            "click_event_db_write_failed",
            extra={
                "event_id": str(event.event_id),
                "link_id": event.link_id,
                "error": str(exc),
            },
        )
        raise

    logger.info(
        "click_event_processed" if inserted else "click_event_duplicate_skipped",
        extra={
            "event_id": str(event.event_id),
            "link_id": event.link_id,
            "processing_ms": round(processing_ms, 2),
        },
    )
    await consumer.commit()
