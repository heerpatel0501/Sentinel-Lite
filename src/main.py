"""
Entrypoint for Member 3's Event Processing + Correlation service.

Usage:
    python -m src.main
"""

import logging

from src.consumer import EventProcessor
from src.rabbitmq_client import RabbitMQClient, load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger("sentinel.main")


def main() -> None:
    config = load_config()
    client = RabbitMQClient(config)
    processor = EventProcessor(client)

    logger.info("Sentinel Lite — Event Processing + Correlation service starting...")
    try:
        processor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down (KeyboardInterrupt)")
    finally:
        client.close()


if __name__ == "__main__":
    main()
