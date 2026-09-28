"""
Consumes raw events from Redis processing queue (`sentinel:queue`), normalizes them,
feeds them through the correlation engine, and republishes normalized events +
any correlated incidents onto Redis Pub/Sub (`sentinel:events`) per ADR-003.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.correlation_engine import CorrelationEngine
from src.models import RawEvent
from src.normalizer import normalize
from src.producer import EventProducer
from src.redis_client import RedisClient

logger = logging.getLogger("sentinel.consumer")


class EventProcessor:
    def __init__(self, client: Optional[Any] = None):
        self.client = client or RedisClient()
        if hasattr(self.client, "connect") and not getattr(self.client, "_connected", False):
            self.client.connect()
        self.config = getattr(self.client, "config", {})
        self.producer = EventProducer(self.client)
        self.engine = CorrelationEngine(self.config)

    def handle_raw_event(self, payload: Dict) -> None:
        raw = RawEvent.from_dict(payload)
        logger.info("Raw event received: %s [%s/%s] zone=%s",
                    raw.event_id, raw.source, raw.event_type, raw.zone_id)

        normalized = normalize(raw, strict=False)
        self.producer.publish_normalized(normalized)

        incidents = self.engine.process(normalized)
        for incident in incidents:
            self.producer.publish_incident(incident)

    def run(self) -> None:
        queue = getattr(self.client, "queue", "sentinel:queue")
        proc_cfg = self.config.get("processing", {})
        max_retries = proc_cfg.get("max_retries", 3)
        self.client.consume(
            queue=queue,
            handler=self.handle_raw_event,
            max_retries=max_retries,
        )
