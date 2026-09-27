"""
Thin wrapper around pika (blocking connection) with:
  - automatic reconnect/retry on startup
  - a helper to publish JSON messages with persistence
  - a helper to consume with manual ack + dead-lettering on repeated failure
"""

from __future__ import annotations

import json
import logging
import time
from typing import Callable, Dict, Optional

import pika
import yaml

logger = logging.getLogger("sentinel.rabbitmq")


def load_config(path: str = "config/config.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


class RabbitMQClient:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_config()
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel: Optional[pika.channel.Channel] = None

    # ------------------------------------------------------------------ #
    # Connection management
    # ------------------------------------------------------------------ #
    def connect(self) -> pika.channel.Channel:
        rmq = self.config["rabbitmq"]
        credentials = pika.PlainCredentials(rmq["user"], rmq["password"])
        params = pika.ConnectionParameters(
            host=rmq["host"],
            port=rmq["port"],
            virtual_host=rmq.get("vhost", "/"),
            credentials=credentials,
            heartbeat=rmq.get("heartbeat", 30),
        )

        attempts = rmq.get("connection_attempts", 5)
        delay = rmq.get("retry_delay_seconds", 3)

        for attempt in range(1, attempts + 1):
            try:
                self._connection = pika.BlockingConnection(params)
                self._channel = self._connection.channel()
                logger.info("Connected to RabbitMQ at %s:%s", rmq["host"], rmq["port"])
                return self._channel
            except pika.exceptions.AMQPConnectionError as exc:
                logger.warning(
                    "RabbitMQ connection attempt %s/%s failed: %s",
                    attempt, attempts, exc,
                )
                if attempt == attempts:
                    raise
                time.sleep(delay)

        raise RuntimeError("Unreachable: exhausted connection attempts")

    def close(self) -> None:
        if self._connection and self._connection.is_open:
            self._connection.close()
            logger.info("RabbitMQ connection closed")

    @property
    def channel(self) -> pika.channel.Channel:
        if self._channel is None or self._channel.is_closed:
            self.connect()
        return self._channel

    # ------------------------------------------------------------------ #
    # Publishing
    # ------------------------------------------------------------------ #
    def publish(self, exchange: str, routing_key: str, payload: Dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # persistent
            ),
        )
        logger.debug("Published to %s [%s]: %s", exchange, routing_key, payload.get("event_id") or payload.get("incident_id"))

    # ------------------------------------------------------------------ #
    # Consuming
    # ------------------------------------------------------------------ #
    def consume(
        self,
        queue: str,
        handler: Callable[[Dict], None],
        prefetch_count: int = 10,
        max_retries: int = 3,
    ) -> None:
        """
        Consume `queue` with manual ack. `handler` receives the decoded JSON
        payload. If `handler` raises, the message is retried up to
        `max_retries` times (tracked via the `x-retry-count` header) before
        being nacked without requeue (routed to the DLX/DLQ).
        """
        ch = self.channel
        ch.basic_qos(prefetch_count=prefetch_count)

        def _on_message(channel, method, properties, body):
            retry_count = 0
            if properties.headers and "x-retry-count" in properties.headers:
                retry_count = properties.headers["x-retry-count"]

            try:
                payload = json.loads(body)
                handler(payload)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception:
                logger.exception("Error processing message (retry_count=%s)", retry_count)
                if retry_count < max_retries:
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    new_headers = dict(properties.headers or {})
                    new_headers["x-retry-count"] = retry_count + 1
                    channel.basic_publish(
                        exchange="",
                        routing_key=queue,
                        body=body,
                        properties=pika.BasicProperties(
                            content_type="application/json",
                            delivery_mode=2,
                            headers=new_headers,
                        ),
                    )
                else:
                    logger.error("Max retries exceeded, sending to DLQ")
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        ch.basic_consume(queue=queue, on_message_callback=_on_message)
        logger.info("Consuming from queue '%s' (prefetch=%s)", queue, prefetch_count)
        try:
            ch.start_consuming()
        except KeyboardInterrupt:
            ch.stop_consuming()
