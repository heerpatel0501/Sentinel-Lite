"""
Normalizes RawEvent (as published by Member 2's VMS/ONVIF adapter or a
sensor) into the canonical NormalizedEvent shape the correlation engine
understands.

Member 2's ONVIF/vendor adapter is responsible for producing RawEvent JSON,
but different camera vendors label event types differently even after
ONVIF translation (e.g. "MotionAlarm" vs "motion_detected" vs "VMD"). This
module is the single place that maps all of those into a small canonical
vocabulary, so correlation rules never have to know about vendor quirks.
"""

from __future__ import annotations

import logging
import uuid
from typing import Dict

from src.models import NormalizedEvent, RawEvent

logger = logging.getLogger("sentinel.normalizer")

# Canonical event types the rest of the system reasons about.
CANONICAL_EVENT_TYPES = {
    "motion_detected",
    "face_detected",
    "door_opened",
    "door_forced",
    "line_crossing",
    "object_left",
    "access_granted",
    "access_denied",
}

# Maps raw/vendor-specific event_type strings -> canonical type.
# Extend this as Member 2 adds new camera vendors / sensor types.
_EVENT_TYPE_ALIASES: Dict[str, str] = {
    "motion_detected": "motion_detected",
    "motionalarm": "motion_detected",
    "vmd": "motion_detected",                 # ONVIF Video Motion Detection
    "face_detected": "face_detected",
    "facedetection": "face_detected",
    "door_opened": "door_opened",
    "dooropen": "door_opened",
    "door_forced": "door_forced",
    "doorforced": "door_forced",
    "line_crossing": "line_crossing",
    "linedetector": "line_crossing",
    "object_left": "object_left",
    "leftobject": "object_left",
    "access_granted": "access_granted",
    "badge_ok": "access_granted",
    "access_denied": "access_denied",
    "badge_denied": "access_denied",
}


class UnknownEventTypeError(ValueError):
    pass


def normalize(raw: RawEvent, strict: bool = False) -> NormalizedEvent:
    """
    Convert a RawEvent into a NormalizedEvent.

    If strict=False (default), unrecognized event_type values pass through
    lower-cased/underscored rather than raising, so the pipeline degrades
    gracefully when Member 2 adds a new camera model before this map is
    updated. Set strict=True in tests to catch mapping gaps.
    """
    key = raw.event_type.strip().lower().replace(" ", "_")
    canonical_type = _EVENT_TYPE_ALIASES.get(key)

    if canonical_type is None:
        if strict:
            raise UnknownEventTypeError(f"No canonical mapping for event_type='{raw.event_type}'")
        logger.warning("Unmapped event_type '%s' — passing through as-is", raw.event_type)
        canonical_type = key

    return NormalizedEvent(
        event_id=str(uuid.uuid4()),
        origin_event_id=raw.event_id,
        camera_or_sensor_id=raw.source,
        source_type=raw.source_type,
        event_type=canonical_type,
        timestamp=raw.timestamp,
        zone_id=raw.zone_id,
        confidence=raw.confidence,
        attributes=raw.metadata,
    )
