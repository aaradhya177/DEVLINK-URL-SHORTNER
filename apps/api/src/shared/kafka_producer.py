import json
import logging
import uuid
from datetime import UTC, datetime
from ipaddress import ip_address, ip_network
from typing import Any

from app.core.config import settings

try:
    from aiokafka import AIOKafkaProducer
except ImportError:  # pragma: no cover - exercised when optional dependency is absent.
    AIOKafkaProducer = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)
CLICK_EVENTS_TOPIC = "click-events"

_producer: Any | None = None


async def publish_click_event(
    link_id: int,
    ip: str,
    user_agent: str | None,
    referrer: str | None,
    timestamp: datetime | None = None,
    event_id: uuid.UUID | None = None,
    correlation_id: str | None = None,
) -> None:
    """Publish one click event without raising to the caller.

    Event schema:
    - event_id: UUID for idempotent worker processing.
    - link_id: database link ID.
    - timestamp: ISO-8601 UTC click time.
    - ip: anonymized source IP for worker-side geolocation and salted hashing.
    - user_agent: raw user-agent string for worker-side parsing.
    - referrer: HTTP referrer, if present.
    """
    if AIOKafkaProducer is None:
        logger.warning("kafka_producer_unavailable")
        return

    occurred_at = timestamp or datetime.now(UTC)
    event = {
        "event_id": str(event_id or uuid.uuid4()),
        "correlation_id": correlation_id,
        "link_id": link_id,
        "timestamp": occurred_at.isoformat(),
        "ip": anonymize_ip_for_geo(ip),
        "user_agent": user_agent,
        "referrer": referrer,
    }

    try:
        producer = await _get_producer()
        await producer.send_and_wait(
            CLICK_EVENTS_TOPIC,
            json.dumps(event, separators=(",", ":")).encode("utf-8"),
            key=str(link_id).encode("utf-8"),
        )
    except Exception as exc:  # pragma: no cover - defensive fire-and-forget boundary.
        logger.warning(
            "click_event_publish_failed",
            extra={
                "link_id": link_id,
                "correlation_id": correlation_id,
                "error": str(exc),
            },
        )


async def _get_producer() -> Any:
    """Lazily create and start the shared Kafka producer."""
    global _producer
    if _producer is not None:
        return _producer

    producer = AIOKafkaProducer(bootstrap_servers=settings.kafka_brokers)
    await producer.start()
    _producer = producer
    return producer


def anonymize_ip_for_geo(raw_ip: str) -> str:
    """Return a coarse IP suitable for geo lookup without storing the raw IP."""
    try:
        parsed_ip = ip_address(raw_ip)
    except ValueError:
        return "0.0.0.0"

    if parsed_ip.version == 4:
        return str(ip_network(f"{parsed_ip}/24", strict=False).network_address)
    return str(ip_network(f"{parsed_ip}/48", strict=False).network_address)
