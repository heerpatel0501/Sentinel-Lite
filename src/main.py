"""
Entrypoint for Member 3's Event Processing + Correlation service (Redis mode per ADR-003).

Usage:
    python -m src.main
"""

import logging

from src.consumer import EventProcessor
from src.redis_client import RedisClient, load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
logger = logging.getLogger("sentinel.main")


def main() -> None:
    config = load_config()
    client = RedisClient(config)
    client.connect()
    processor = EventProcessor(client)

    logger.info("Sentinel Lite — Event Processing + Correlation service starting (Redis mode)...")
    try:
        processor.run()
    except KeyboardInterrupt:
        logger.info("Shutting down (KeyboardInterrupt)")
    finally:
        client.close()


if __name__ == "__main__":
    main()
