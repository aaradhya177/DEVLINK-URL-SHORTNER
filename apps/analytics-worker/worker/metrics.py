from prometheus_client import Counter, Gauge, Histogram, start_http_server


click_events_processed_total = Counter(
    "devlink_worker_click_events_processed_total",
    "Click events processed by the analytics worker.",
    ["result"],
)

click_event_processing_seconds = Histogram(
    "devlink_worker_click_event_processing_seconds",
    "Time spent processing one click event.",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5),
)

kafka_consumer_lag = Gauge(
    "devlink_worker_kafka_consumer_lag",
    "Approximate Kafka consumer lag by topic and partition.",
    ["topic", "partition"],
)


def start_metrics_server(port: int) -> None:
    """Expose worker Prometheus metrics on an internal HTTP port."""
    start_http_server(port)
