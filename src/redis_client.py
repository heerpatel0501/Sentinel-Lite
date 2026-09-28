"""
Redis client wrapper for Member 3's Event Processing + Correlation pipeline (ADR-003).
Provides Redis Pub/Sub and list queue operations with clear connection logging and DLQ support.
Replaces legacy RabbitMQ client per ADR-003.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("sentinel.redis")


def load_config() -> dict:
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml")
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}


class RedisClient:
    """
    Unified Redis messaging client for Sentinel-Lite.
    Supports Pub/Sub (sentinel:events) for live fanout and list queue (sentinel:queue)
    for worker processing, with DLQ (sentinel:queue:dlq) for failed messages.
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        redis_cfg = self.config.get("redis", {})
        self.url = os.getenv("REDIS_URL", redis_cfg.get("url", "redis://localhost:6379/0"))
        self.channel = redis_cfg.get("channels", {}).get("events", "sentinel:events")
        self.queue = redis_cfg.get("queues", {}).get("raw_processing", "sentinel:queue")
        self.dlq = redis_cfg.get("queues", {}).get("dead_letter", "sentinel:queue:dlq")
        self._client = None
        self._connected = False

    def connect(self):
        """Connects and validates PING to Redis service."""
        try:
            import redis
            self._client = redis.Redis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=5.0
            )
            self._client.ping()
            self._connected = True
            logger.info("Connected to Redis at %s", self.url)
            logger.info("Redis Pub/Sub channel: %s | Queue: %s | DLQ: %s", self.channel, self.queue, self.dlq)
            return self._client
        except Exception as e:
            self._connected = False
            logger.warning("Redis connection failed at %s: %s", self.url, e)
            return None

    def publish(self, channel: Optional[str], message: dict) -> None:
        """Publishes to Redis Pub/Sub and pushes to queue."""
        target_channel = channel or self.channel
        payload = json.dumps(message, default=str)
        if self._client and self._connected:
            self._client.publish(target_channel, payload)
            if target_channel == self.channel:
                self._client.rpush(self.queue, payload)
        else:
            logger.debug("[Fallback] Published event to %s", target_channel)

    def enqueue(self, queue: Optional[str], message: dict) -> None:
        """Enqueues message into list queue."""
        target_queue = queue or self.queue
        payload = json.dumps(message, default=str)
        if self._client and self._connected:
            self._client.rpush(target_queue, payload)

    def consume_one(self, queue: Optional[str] = None) -> Optional[dict]:
        """Pops one message from Redis list queue."""
        target_queue = queue or self.queue
        if self._client and self._connected:
            item = self._client.lpop(target_queue)
            if item:
                return json.loads(item)
        return None

    def consume(self, queue: Optional[str] = None, handler: Optional[Callable[[dict], None]] = None, max_retries: int = 3) -> None:
        """Continuous consumption loop with retry & DLQ handling."""
        target_queue = queue or self.queue
        if not self._connected or not self._client:
            logger.warning("Redis not connected; cannot start consume loop for %s", target_queue)
            return

        logger.info("Consuming from Redis queue: %s", target_queue)
        while True:
            try:
                item = self._client.lpop(target_queue)
                if not item:
                    time.sleep(0.1)
                    continue

                data = json.loads(item)
                try:
                    if handler:
                        handler(data)
                except Exception as ex:
                    retry = data.get("_retry_count", 0) + 1
                    data["_retry_count"] = retry
                    data["_error"] = str(ex)
                    if retry >= max_retries:
                        data["_dead_lettered_at"] = time.time()
                        self._client.rpush(self.dlq, json.dumps(data, default=str))
                        logger.error("Message routed to DLQ %s after %s retries: %s", self.dlq, retry, ex)
                    else:
                        self._client.rpush(target_queue, json.dumps(data, default=str))
            except Exception as e:
                logger.error("Consumer loop exception: %s", e)

    def close(self) -> None:
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            logger.info("Redis connection closed")
