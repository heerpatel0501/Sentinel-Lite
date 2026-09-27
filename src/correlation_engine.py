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
        c = config["correlation"]
        self.window_seconds = c["window_seconds"]
        self.loitering_motion_threshold = c["loitering_motion_threshold"]
        self.loitering_window_seconds = c["loitering_window_seconds"]
        self.tailgate_line_crossing_threshold = c["tailgate_line_crossing_threshold"]
        self.tailgate_window_seconds = c["tailgate_window_seconds"]
        self.confidence_boost = c["confidence_boost_per_event"]
        self.max_confidence = c["max_confidence"]

        # Use the largest window needed by any rule so the store retains enough history.
        widest = max(self.window_seconds, self.loitering_window_seconds, self.tailgate_window_seconds)
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

        for rule in (self._rule_intrusion, self._rule_loitering, self._rule_tailgating):
            incident = rule(event, window)
            if incident and not self._is_on_cooldown(incident):
                incidents.append(incident)
                self._mark_fired(incident)

        return incidents

    def _is_on_cooldown(self, incident: CorrelatedIncident) -> bool:
        key = f"{incident.zone_id}:{incident.incident_type}"
        last_fired = self._recent_incidents.get(key)
        if last_fired is None:
            return False
        return (_parse_ts(incident.last_seen) - last_fired) < self._incident_cooldown

    def _mark_fired(self, incident: CorrelatedIncident) -> None:
        key = f"{incident.zone_id}:{incident.incident_type}"
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
