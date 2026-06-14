import json
import logging

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import TopicPartition
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from worker.aggregator import process_click_event
from worker.config import settings
from worker.db import async_session_factory
from worker.events import ClickEventMessage
from worker.metrics import (
    click_event_processing_seconds,
    click_events_processed_total,
    kafka_consumer_lag,
)


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
        click_events_processed_total.labels(result="malformed").inc()
        await consumer.commit()
        return

    _record_consumer_lag(consumer, message)
    try:
        async with async_session_factory() as session:
            inserted, processing_ms = await process_click_event(session, event)
    except SQLAlchemyError as exc:
        logger.exception(
            "click_event_db_write_failed",
            extra={
                "event_id": str(event.event_id),
                "correlation_id": event.correlation_id,
                "link_id": event.link_id,
                "error": str(exc),
            },
        )
        raise

    click_event_processing_seconds.observe(processing_ms / 1000)
    click_events_processed_total.labels(
        result="processed" if inserted else "duplicate"
    ).inc()
    logger.info(
        "click_event_processed" if inserted else "click_event_duplicate_skipped",
        extra={
            "event_id": str(event.event_id),
            "correlation_id": event.correlation_id,
            "link_id": event.link_id,
            "processing_ms": round(processing_ms, 2),
        },
    )
    await consumer.commit()


def _record_consumer_lag(consumer: AIOKafkaConsumer, message: object) -> None:
    """Record best-effort consumer lag without failing event processing."""
    topic = getattr(message, "topic", None)
    partition = getattr(message, "partition", None)
    offset = getattr(message, "offset", None)
    if topic is None or partition is None or offset is None:
        return

    highwater = consumer.highwater(TopicPartition(topic, partition))
    if highwater is None:
        return
    kafka_consumer_lag.labels(topic=topic, partition=str(partition)).set(
        max(highwater - offset - 1, 0)
    )
