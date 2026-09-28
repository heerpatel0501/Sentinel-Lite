"""
Redis Messaging Topology Manager (ADR-003).

Declares and verifies the unified Redis messaging topology for Sentinel-Lite:
  - Realtime Fanout (Redis Pub/Sub): sentinel:events
  - Ingestion / Worker Queue (Redis List): sentinel:queue
  - Dead Letter Queue (Redis List): sentinel:queue:dlq

Replaces legacy RabbitMQ topology per ADR-003.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.redis_client import RedisClient, load_config

logger = logging.getLogger("sentinel.topology")


def declare_topology(client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Verifies and initializes the Redis messaging topology for Sentinel-Lite.
    Returns a dictionary summarizing active channels, queues, and queue lengths.
    """
    if client is None:
        client = RedisClient(load_config())

    if hasattr(client, "connect") and not getattr(client, "_connected", False):
        client.connect()

    channel = getattr(client, "channel", "sentinel:events")
    queue = getattr(client, "queue", "sentinel:queue")
    dlq = getattr(client, "dlq", "sentinel:queue:dlq")

    is_connected = getattr(client, "_connected", False)
    topology_info: Dict[str, Any] = {
        "mode": "redis" if is_connected else "in-memory fallback",
        "channel": channel,
        "queue": queue,
        "dlq": dlq,
        "queue_length": 0,
        "dlq_length": 0,
    }

    if is_connected and getattr(client, "_client", None) is not None:
        try:
            topology_info["queue_length"] = client._client.llen(queue)
            topology_info["dlq_length"] = client._client.llen(dlq)
            logger.info("Redis Messaging Topology (ADR-003) verified:")
            logger.info("  Ingestion Queue (Redis List):   %s (length: %d)", queue, topology_info["queue_length"])
            logger.info("  Realtime Fanout (Redis Pub/Sub): %s", channel)
            logger.info("  Dead Letter Queue (Redis List):  %s (length: %d)", dlq, topology_info["dlq_length"])
        except Exception as exc:
            logger.warning("Error inspecting Redis queue metrics: %s", exc)
    else:
        logger.info("Redis unavailable; development in-memory fallback active.")
        logger.info("Configured topology: Queue: %s | Pub/Sub: %s | DLQ: %s", queue, channel, dlq)

    return topology_info


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    client = RedisClient(load_config())
    info = declare_topology(client)
    print("\n" + "=" * 60)
    print("SENTINEL-LITE REDIS TOPOLOGY STATUS (ADR-003)")
    print("=" * 60)
    print(f"Execution Mode:       {info['mode'].upper()}")
    print(f"Pub/Sub Channel:      {info['channel']}")
    print(f"Worker Queue:         {info['queue']} (length: {info['queue_length']})")
    print(f"Dead Letter Queue:    {info['dlq']} (length: {info['dlq_length']})")
    print("=" * 60 + "\n")
    client.close()
