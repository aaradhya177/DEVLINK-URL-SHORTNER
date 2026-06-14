import json
import logging
import sys
from typing import Any


class JsonFormatter(logging.Formatter):
    """Format log records as compact JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Return a JSON log line."""
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("event_id", "link_id", "processing_ms", "error"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(level: str) -> None:
    """Configure structured JSON logging for the worker."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
