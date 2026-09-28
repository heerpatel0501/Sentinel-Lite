"""
Unit tests for the correlation engine — no RabbitMQ required.

Run with:  pytest tests/ -v
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.correlation_engine import CorrelationEngine  # noqa: E402
from src.models import NormalizedEvent  # noqa: E402

BASE_TIME = datetime(2026, 9, 26, 10, 0, 0, tzinfo=timezone.utc)


def ts(offset_seconds: float) -> str:
    return (BASE_TIME + timedelta(seconds=offset_seconds)).isoformat()


def event(event_type, zone="zone_lobby", camera="camera_01", offset=0.0, confidence=0.9):
    return NormalizedEvent(
        event_id=f"evt-{event_type}-{offset}",
        origin_event_id="origin",
        camera_or_sensor_id=camera,
        source_type="camera",
        event_type=event_type,
        timestamp=ts(offset),
        zone_id=zone,
        confidence=confidence,
        attributes={},
    )


@pytest.fixture
def config():
    return {
        "correlation": {
            "window_seconds": 30,
            "loitering_motion_threshold": 3,
            "loitering_window_seconds": 60,
            "tailgate_line_crossing_threshold": 2,
            "tailgate_window_seconds": 8,
            "confidence_boost_per_event": 0.1,
            "max_confidence": 1.0,
        }
    }


def test_intrusion_fires_on_motion_plus_door_no_badge(config):
    engine = CorrelationEngine(config)
    incidents = engine.process(event("motion_detected", offset=0))
    assert incidents == []

    incidents = engine.process(event("door_opened", offset=2))
    assert len(incidents) == 1
    assert incidents[0].incident_type == "intrusion_suspected"
    assert incidents[0].zone_id == "zone_lobby"


def test_intrusion_does_not_fire_with_access_granted(config):
    engine = CorrelationEngine(config)
    engine.process(event("access_granted", offset=0))
    engine.process(event("motion_detected", offset=1))
    incidents = engine.process(event("door_opened", offset=2))
    assert incidents == []


def test_forced_entry_variant(config):
    engine = CorrelationEngine(config)
    engine.process(event("motion_detected", offset=0))
    incidents = engine.process(event("door_forced", offset=1))
    assert len(incidents) == 1
    assert incidents[0].incident_type == "forced_entry_suspected"


def test_loitering_fires_after_threshold_motions_no_face(config):
    engine = CorrelationEngine(config)
    engine.process(event("motion_detected", camera="cam_park", offset=0))
    engine.process(event("motion_detected", camera="cam_park", offset=15))
    incidents = engine.process(event("motion_detected", camera="cam_park", offset=30))
    assert len(incidents) == 1
    assert incidents[0].incident_type == "loitering_suspected"


def test_loitering_suppressed_when_face_resolved(config):
    engine = CorrelationEngine(config)
    engine.process(event("motion_detected", camera="cam_park", offset=0))
    engine.process(event("face_detected", camera="cam_park", offset=5))
    engine.process(event("motion_detected", camera="cam_park", offset=15))
    incidents = engine.process(event("motion_detected", camera="cam_park", offset=30))
    assert incidents == []


def test_tailgating_fires_on_multiple_crossings_after_one_grant(config):
    engine = CorrelationEngine(config)
    engine.process(event("access_granted", zone="zone_entrance", offset=0))
    engine.process(event("line_crossing", zone="zone_entrance", offset=1))
    engine.process(event("line_crossing", zone="zone_entrance", offset=2))
    incidents = engine.process(event("line_crossing", zone="zone_entrance", offset=3))
    assert len(incidents) == 1
    assert incidents[0].incident_type == "tailgating_suspected"


def test_confidence_boost_increases_with_more_contributing_events(config):
    engine = CorrelationEngine(config)
    engine.process(event("motion_detected", offset=0, confidence=0.7))
    engine.process(event("motion_detected", offset=1, confidence=0.7))
    incidents = engine.process(event("door_opened", offset=2, confidence=0.8))
    assert incidents[0].confidence > 0.8  # boosted above the max base confidence


def test_incident_cooldown_prevents_duplicate_firing(config):
    engine = CorrelationEngine(config)
    engine.process(event("motion_detected", offset=0))
    first = engine.process(event("door_opened", offset=2))
    assert len(first) == 1

    # Another motion event shortly after, same zone -> rule matches again,
    # but cooldown should suppress a duplicate incident.
    second = engine.process(event("motion_detected", offset=4))
    assert second == []


def test_cross_camera_motion_correlation(config):
    engine = CorrelationEngine(config)
    # Camera A detects motion
    engine.process(event("motion_detected", camera="cam_a", offset=0))
    # Camera B detects motion in same zone
    incidents = engine.process(event("motion_detected", camera="cam_b", offset=5))
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.incident_type == "cross_camera_motion"
    assert "cam_a" in inc.metadata["camera_ids"]
    assert "cam_b" in inc.metadata["camera_ids"]
    assert inc.metadata["candidate_status"] == "candidate"


def test_cross_department_plate_correlation(config):
    engine = CorrelationEngine(config)
    # Traffic department camera observes plate
    evt1 = NormalizedEvent(
        event_id="evt-plate-1",
        origin_event_id="orig-1",
        camera_or_sensor_id="traffic_cam_01",
        source_type="camera",
        event_type="plate_recognition",
        timestamp=ts(0),
        zone_id="zone_highway",
        confidence=0.92,
        attributes={"plate": "GJ01-AB-1234", "department": "RTO"},
    )
    engine.process(evt1)

    # Police department camera observes same plate
    evt2 = NormalizedEvent(
        event_id="evt-plate-2",
        origin_event_id="orig-2",
        camera_or_sensor_id="police_cam_02",
        source_type="camera",
        event_type="plate_recognition",
        timestamp=ts(10),
        zone_id="zone_highway",
        confidence=0.95,
        attributes={"plate": "GJ01-AB-1234", "department": "Police"},
    )
    incidents = engine.process(evt2)
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.incident_type == "cross_department_sighting"
    assert "Police" in inc.metadata["departments"]
    assert "RTO" in inc.metadata["departments"]
    assert inc.metadata["plate_text"] == "GJ01-AB-1234"
    assert inc.metadata["candidate_status"] == "candidate"

