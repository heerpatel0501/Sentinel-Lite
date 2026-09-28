"""
Sliding-window correlation engine.

Design
------
For each `zone_id`, we keep a deque of recently normalized events (pruned by
age on every insert). Whenever a new event arrives, we re-evaluate a small
set of rules against that zone's current window. A rule that fires produces
a CorrelatedIncident.

This is intentionally in-memory / single-process for "Lite" scope. For a
multi-instance deployment you'd back the window store with Redis (Member 5
already runs Redis) keyed by zone_id with a sorted set — the rule functions
below would not need to change, only `EventWindowStore`.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Deque, Dict, List, Optional

from dateutil import parser as dateparser

from src.models import CorrelatedIncident, NormalizedEvent

logger = logging.getLogger("sentinel.correlation")


def _parse_ts(ts: str) -> datetime:
    dt = dateparser.isoparse(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


class EventWindowStore:
    """Keeps a rolling per-zone window of NormalizedEvents."""

    def __init__(self, max_window_seconds: int):
        self.max_window_seconds = max_window_seconds
        self._zones: Dict[str, Deque[NormalizedEvent]] = defaultdict(deque)

    def add(self, event: NormalizedEvent) -> List[NormalizedEvent]:
        """Add event, prune stale ones, and return the current window for its zone."""
        window = self._zones[event.zone_id]
        window.append(event)
        self._prune(window)
        return list(window)

    def _prune(self, window: Deque[NormalizedEvent]) -> None:
        if not window:
            return
        newest_ts = _parse_ts(window[-1].timestamp)
        cutoff = newest_ts - timedelta(seconds=self.max_window_seconds)
        while window and _parse_ts(window[0].timestamp) < cutoff:
            window.popleft()


class CorrelationEngine:
    def __init__(self, config: dict):
        c = config.get("correlation", config)
        self.window_seconds = c.get("window_seconds", 30)
        self.loitering_motion_threshold = c.get("loitering_motion_threshold", 3)
        self.loitering_window_seconds = c.get("loitering_window_seconds", 60)
        self.tailgate_line_crossing_threshold = c.get("tailgate_line_crossing_threshold", 2)
        self.tailgate_window_seconds = c.get("tailgate_window_seconds", 8)
        self.motion_camera_threshold = c.get("motion_correlation_camera_threshold", 2)
        self.cross_dept_threshold = c.get("cross_dept_threshold", 2)
        self.confidence_boost = c.get("confidence_boost_per_event", 0.1)
        self.max_confidence = c.get("max_confidence", 1.0)

        # Use the largest window needed by any rule so the store retains enough history.
        widest = max(
            self.window_seconds,
            self.loitering_window_seconds,
            self.tailgate_window_seconds
        )
        self.store = EventWindowStore(max_window_seconds=widest)

        # Dedup: avoid re-raising the same incident type for the same zone
        # every time a new contributing event arrives within a short span.
        self._recent_incidents: Dict[str, datetime] = {}
        self._incident_cooldown = timedelta(seconds=self.window_seconds)

    # ------------------------------------------------------------------ #
    def process(self, event: NormalizedEvent) -> List[CorrelatedIncident]:
        """Feed one normalized event through the engine; returns 0+ incidents."""
        window = self.store.add(event)
        incidents: List[CorrelatedIncident] = []

        for rule in (
            self._rule_intrusion,
            self._rule_loitering,
            self._rule_tailgating,
            self._rule_cross_camera_motion,
            self._rule_cross_department_plate,
        ):
            incident = rule(event, window)
            if incident and not self._is_on_cooldown(incident):
                incidents.append(incident)
                self._mark_fired(incident)

        return incidents

    def _is_on_cooldown(self, incident: CorrelatedIncident) -> bool:
        plate = incident.metadata.get("plate_text", "")
        key = f"{incident.zone_id}:{incident.incident_type}:{plate}"
        last_fired = self._recent_incidents.get(key)
        if last_fired is None:
            return False
        return (_parse_ts(incident.last_seen) - last_fired) < self._incident_cooldown

    def _mark_fired(self, incident: CorrelatedIncident) -> None:
        plate = incident.metadata.get("plate_text", "")
        key = f"{incident.zone_id}:{incident.incident_type}:{plate}"
        self._recent_incidents[key] = _parse_ts(incident.last_seen)

    def _score(self, base_confidences: List[float]) -> float:
        base = max(base_confidences)
        boost = self.confidence_boost * (len(base_confidences) - 1)
        return min(base + boost, self.max_confidence)

    # ------------------------------------------------------------------ #
    # Rule 1: Intrusion suspected
    #   motion_detected + (door_opened|door_forced|line_crossing) in the
    #   same zone within `window_seconds`, with NO access_granted event
    #   covering the same window (i.e. nobody badged in).
    # ------------------------------------------------------------------ #
    def _rule_intrusion(self, event: NormalizedEvent, window: List[NormalizedEvent]) -> Optional[CorrelatedIncident]:
        cutoff = _parse_ts(event.timestamp) - timedelta(seconds=self.window_seconds)
        recent = [e for e in window if _parse_ts(e.timestamp) >= cutoff]

        motions = [e for e in recent if e.event_type == "motion_detected"]
        entries = [e for e in recent if e.event_type in ("door_opened", "door_forced", "line_crossing")]
        granted = [e for e in recent if e.event_type == "access_granted"]

        if motions and entries and not granted:
            contributing = motions + entries
            incident_type = "intrusion_suspected"
            if any(e.event_type == "door_forced" for e in entries):
                incident_type = "forced_entry_suspected"

            confidence = self._score([e.confidence for e in contributing])
            summary = (
                f"{len(motions)} motion event(s) and {len(entries)} entry event(s) "
                f"in zone '{event.zone_id}' within {self.window_seconds}s with no access badge-in."
            )
            return CorrelatedIncident.new(
                incident_type=incident_type,
                zone_id=event.zone_id,
                confidence=confidence,
                contributing=contributing,
                summary=summary,
            )
        return None

    # ------------------------------------------------------------------ #
    # Rule 2: Loitering suspected
    #   >= N motion_detected events from the SAME camera within a longer
    #   window, without a corresponding face_detected (i.e. sustained
    #   presence/movement without a clear identified subject leaving).
    # ------------------------------------------------------------------ #
    def _rule_loitering(self, event: NormalizedEvent, window: List[NormalizedEvent]) -> Optional[CorrelatedIncident]:
        if event.event_type != "motion_detected":
            return None

        cutoff = _parse_ts(event.timestamp) - timedelta(seconds=self.loitering_window_seconds)
        same_camera_motions = [
            e for e in window
            if e.event_type == "motion_detected"
            and e.camera_or_sensor_id == event.camera_or_sensor_id
            and _parse_ts(e.timestamp) >= cutoff
        ]

        if len(same_camera_motions) >= self.loitering_motion_threshold:
            faces_in_window = [
                e for e in window
                if e.event_type == "face_detected"
                and e.camera_or_sensor_id == event.camera_or_sensor_id
                and _parse_ts(e.timestamp) >= cutoff
            ]
            if not faces_in_window:
                confidence = self._score([e.confidence for e in same_camera_motions])
                summary = (
                    f"{len(same_camera_motions)} motion events from camera "
                    f"'{event.camera_or_sensor_id}' within {self.loitering_window_seconds}s, "
                    f"no face resolved."
                )
                return CorrelatedIncident.new(
                    incident_type="loitering_suspected",
                    zone_id=event.zone_id,
                    confidence=confidence,
                    contributing=same_camera_motions,
                    summary=summary,
                )
        return None

    # ------------------------------------------------------------------ #
    # Rule 3: Tailgating suspected
    #   one access_granted event followed by more than
    #   `tailgate_line_crossing_threshold` line_crossing events in the same
    #   zone within a short window (one badge, multiple people through).
    # ------------------------------------------------------------------ #
    def _rule_tailgating(self, event: NormalizedEvent, window: List[NormalizedEvent]) -> Optional[CorrelatedIncident]:
        if event.event_type != "line_crossing":
            return None

        cutoff = _parse_ts(event.timestamp) - timedelta(seconds=self.tailgate_window_seconds)
        recent = [e for e in window if _parse_ts(e.timestamp) >= cutoff]

        grants = [e for e in recent if e.event_type == "access_granted"]
        crossings = [e for e in recent if e.event_type == "line_crossing"]

        if grants and len(crossings) > self.tailgate_line_crossing_threshold:
            contributing = grants + crossings
            confidence = self._score([e.confidence for e in contributing])
            summary = (
                f"{len(crossings)} line crossings following a single access grant "
                f"in zone '{event.zone_id}' within {self.tailgate_window_seconds}s."
            )
            return CorrelatedIncident.new(
                incident_type="tailgating_suspected",
                zone_id=event.zone_id,
                confidence=confidence,
                contributing=contributing,
                summary=summary,
            )
        return None

    # ------------------------------------------------------------------ #
    # Rule 4: Multi-Camera Motion Correlation
    #   Related motion/vehicle events observed across >= N distinct cameras
    #   within the zone window.
    # ------------------------------------------------------------------ #
    def _rule_cross_camera_motion(self, event: NormalizedEvent, window: List[NormalizedEvent]) -> Optional[CorrelatedIncident]:
        valid_motion_types = {"motion_detected", "vehicle_detection", "line_crossing", "object_left"}
        if event.event_type not in valid_motion_types:
            return None

        cutoff = _parse_ts(event.timestamp) - timedelta(seconds=self.window_seconds)
        recent_motions = [
            e for e in window
            if e.event_type in valid_motion_types
            and _parse_ts(e.timestamp) >= cutoff
        ]

        distinct_cameras = {}
        for e in recent_motions:
            if e.camera_or_sensor_id not in distinct_cameras:
                distinct_cameras[e.camera_or_sensor_id] = e

        if len(distinct_cameras) >= self.motion_camera_threshold:
            contributing = list(distinct_cameras.values())
            camera_ids = list(distinct_cameras.keys())
            confidence = self._score([e.confidence for e in contributing])
            summary = (
                f"Multi-camera motion sequence tracked across {len(camera_ids)} cameras "
                f"({', '.join(camera_ids)}) in zone '{event.zone_id}' within {self.window_seconds}s."
            )
            metadata = {
                "camera_ids": camera_ids,
                "source_event_ids": [e.origin_event_id or e.event_id for e in contributing],
                "timestamps": [e.timestamp for e in contributing],
                "event_types": [e.event_type for e in contributing],
                "correlation_reason": "Sequential motion tracking across multiple camera viewpoints",
                "candidate_status": "candidate",
            }
            return CorrelatedIncident.new(
                incident_type="cross_camera_motion",
                zone_id=event.zone_id,
                confidence=confidence,
                contributing=contributing,
                summary=summary,
                metadata=metadata,
            )
        return None

    # ------------------------------------------------------------------ #
    # Rule 5: Cross-Department Plate Sightings
    #   Target vehicle plate observed across >= 2 distinct departments
    #   within the correlation window.
    # ------------------------------------------------------------------ #
    def _rule_cross_department_plate(self, event: NormalizedEvent, window: List[NormalizedEvent]) -> Optional[CorrelatedIncident]:
        plate = (
            event.attributes.get("plate_text")
            or event.attributes.get("plate")
            or event.attributes.get("plate_number")
        )
        if not plate:
            return None

        clean_plate = str(plate).strip().upper().replace(" ", "").replace("-", "")
        cutoff = _parse_ts(event.timestamp) - timedelta(seconds=self.window_seconds)

        matching_events = []
        dept_map = {}
        for e in window:
            if _parse_ts(e.timestamp) < cutoff:
                continue
            e_plate = (
                e.attributes.get("plate_text")
                or e.attributes.get("plate")
                or e.attributes.get("plate_number")
            )
            if not e_plate:
                continue
            if str(e_plate).strip().upper().replace(" ", "").replace("-", "") == clean_plate:
                matching_events.append(e)
                dept = (
                    e.attributes.get("department")
                    or e.attributes.get("source_department")
                    or e.source_type
                )
                if dept:
                    dept_map[str(dept)] = e

        if len(dept_map) >= self.cross_dept_threshold:
            contributing = matching_events
            depts = sorted(list(dept_map.keys()))
            cams = sorted(list(set(e.camera_or_sensor_id for e in contributing)))
            confidence = self._score([e.confidence for e in contributing])
            summary = (
                f"Cross-department sighting of plate '{plate}' tracked across "
                f"{len(depts)} departments ({', '.join(depts)}) at cameras {', '.join(cams)}."
            )
            metadata = {
                "plate_text": plate,
                "departments": depts,
                "camera_ids": cams,
                "source_event_ids": [e.origin_event_id or e.event_id for e in contributing],
                "timestamps": [e.timestamp for e in contributing],
                "event_types": [e.event_type for e in contributing],
                "correlation_reason": f"Cross-department target sighting across {', '.join(depts)}",
                "candidate_status": "candidate",
            }
            return CorrelatedIncident.new(
                incident_type="cross_department_sighting",
                zone_id=event.zone_id,
                confidence=confidence,
                contributing=contributing,
                summary=summary,
                metadata=metadata,
            )
        return None

