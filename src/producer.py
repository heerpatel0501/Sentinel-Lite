"""
Publishes NormalizedEvent and CorrelatedIncident objects onto the
`sentinel.processed_events` exchange for Member 4 (dashboard) and
Member 6 (AI/analytics) to consume.
"""

from __future__ import annotations

import logging

from src.models import CorrelatedIncident, NormalizedEvent
from src.rabbitmq_client import RabbitMQClient

logger = logging.getLogger("sentinel.producer")


class EventProducer:
    def __init__(self, client: RabbitMQClient):
        self.client = client
        self.exchange = client.config["exchanges"]["processed_events"]

    def publish_normalized(self, event: NormalizedEvent) -> None:
        routing_key = f"normalized.{event.event_type}"
        self.client.publish(self.exchange, routing_key, event.to_dict())
        logger.debug("Published normalized event %s (%s)", event.event_id, routing_key)

    def publish_incident(self, incident: CorrelatedIncident) -> None:
        routing_key = f"correlated.{incident.incident_type}"
        self.client.publish(self.exchange, routing_key, incident.to_dict())
        logger.info(
            "CORRELATED INCIDENT [%s] zone=%s confidence=%.2f — %s",
            incident.incident_type, incident.zone_id, incident.confidence, incident.summary,
        )
