"""
Canonical event schemas used across the pipeline.

RawEvent        -> whatever Member 2 (VMS/CCTV) or a sensor publishes.
NormalizedEvent -> vendor-agnostic internal representation Member 3 works with.
CorrelatedIncident -> output of the correlation engine, consumed by
                      Member 4 (dashboard) and Member 6 (AI/analytics).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RawEvent:
    event_id: str
    source: str                 # e.g. "camera_01", "door_sensor_lobby"
    source_type: str            # "camera" | "sensor" | "vms"
    event_type: str             # e.g. "motion_detected", "door_opened"
    timestamp: str              # ISO8601
    zone_id: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "RawEvent":
        return RawEvent(
            event_id=d.get("event_id", str(uuid.uuid4())),
            source=d["source"],
            source_type=d["source_type"],
            event_type=d["event_type"],
            timestamp=d.get("timestamp", utc_now_iso()),
            zone_id=d.get("zone_id", "unknown_zone"),
            confidence=float(d.get("confidence", 1.0)),
            metadata=d.get("metadata", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NormalizedEvent:
    """Vendor-agnostic event. All downstream logic operates on this shape."""
    event_id: str
    origin_event_id: str        # id of the RawEvent this came from
    camera_or_sensor_id: str
    source_type: str
    event_type: str             # canonical type, see normalizer.CANONICAL_EVENT_TYPES
    timestamp: str
    zone_id: str
    confidence: float
    attributes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CorrelatedIncident:
    incident_id: str
    incident_type: str          # e.g. "intrusion_suspected"
    zone_id: str
    confidence: float
    first_seen: str
    last_seen: str
    contributing_events: List[str]   # NormalizedEvent event_ids
    summary: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def new(incident_type: str, zone_id: str, confidence: float,
            contributing: List[NormalizedEvent], summary: str,
            metadata: Optional[Dict[str, Any]] = None) -> "CorrelatedIncident":
        timestamps = sorted(e.timestamp for e in contributing)
        return CorrelatedIncident(
            incident_id=str(uuid.uuid4()),
            incident_type=incident_type,
            zone_id=zone_id,
            confidence=round(min(confidence, 1.0), 3),
            first_seen=timestamps[0],
            last_seen=timestamps[-1],
            contributing_events=[e.event_id for e in contributing],
            summary=summary,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
