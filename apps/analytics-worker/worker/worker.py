import asyncio

from worker.consumer import consume_click_events
from worker.config import settings
from worker.logging_utils import configure_logging


def main() -> None:
    """Run the analytics worker event loop."""
    configure_logging(settings.log_level)
    asyncio.run(consume_click_events())


if __name__ == "__main__":
    main()
