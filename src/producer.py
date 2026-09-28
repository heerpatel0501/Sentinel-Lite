"""
Publishes NormalizedEvent and CorrelatedIncident objects onto Redis Pub/Sub (`sentinel:events`)
and processing queue (`sentinel:queue`) for Member 4 (dashboard/WebSocket) and
Member 6 (AI/analytics) to consume per ADR-003.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.models import CorrelatedIncident, NormalizedEvent
from src.redis_client import RedisClient

logger = logging.getLogger("sentinel.producer")


class EventProducer:
    def __init__(self, client: Optional[Any] = None):
        self.client = client or RedisClient()
        if hasattr(self.client, "connect") and not getattr(self.client, "_connected", False):
            self.client.connect()
        self.channel = getattr(self.client, "channel", "sentinel:events")

    def publish_normalized(self, event: NormalizedEvent) -> None:
        payload = event.to_dict()
        if hasattr(self.client, "publish"):
            try:
                self.client.publish(self.channel, payload)
            except TypeError:
                self.client.publish(self.channel, f"normalized.{event.event_type}", payload)
        logger.debug("Published normalized event %s (%s)", event.event_id, event.event_type)

    def publish_incident(self, incident: CorrelatedIncident) -> None:
        payload = incident.to_dict()
        if hasattr(self.client, "publish"):
            try:
                self.client.publish(self.channel, payload)
            except TypeError:
                self.client.publish(self.channel, f"correlated.{incident.incident_type}", payload)
        logger.info(
            "CORRELATED INCIDENT [%s] zone=%s confidence=%.2f — %s",
            incident.incident_type, incident.zone_id, incident.confidence, incident.summary,
        )
