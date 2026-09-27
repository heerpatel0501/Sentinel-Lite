"""
Consumes raw events from `event_processing.raw`, normalizes them, feeds
them through the correlation engine, and republishes normalized events +
any correlated incidents.
"""

from __future__ import annotations

import logging
from typing import Dict

from src.correlation_engine import CorrelationEngine
from src.models import RawEvent
from src.normalizer import normalize
from src.producer import EventProducer
from src.rabbitmq_client import RabbitMQClient

logger = logging.getLogger("sentinel.consumer")


class EventProcessor:
    def __init__(self, client: RabbitMQClient):
        self.client = client
        self.config = client.config
        self.producer = EventProducer(client)
        self.engine = CorrelationEngine(client.config)

    def handle_raw_event(self, payload: Dict) -> None:
        raw = RawEvent.from_dict(payload)
        logger.info("Raw event received: %s [%s/%s] zone=%s",
                    raw.event_id, raw.source, raw.event_type, raw.zone_id)

        normalized = normalize(raw)
        self.producer.publish_normalized(normalized)

        incidents = self.engine.process(normalized)
        for incident in incidents:
            self.producer.publish_incident(incident)

    def run(self) -> None:
        queue = self.config["queues"]["raw_processing"]
        proc_cfg = self.config.get("processing", {})
        self.client.consume(
            queue=queue,
            handler=self.handle_raw_event,
            prefetch_count=proc_cfg.get("prefetch_count", 10),
            max_retries=proc_cfg.get("max_retries", 3),
        )
