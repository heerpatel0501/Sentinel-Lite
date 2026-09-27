"""
Simulates Member 2 (VMS/CCTV integration) publishing raw events onto
`sentinel.raw_events`, so Member 3's pipeline can be exercised end-to-end
without real cameras/sensors.

Usage:
    python scripts/publish_test_events.py --scenario intrusion
    python scripts/publish_test_events.py --scenario loitering
    python scripts/publish_test_events.py --scenario tailgating
    python scripts/publish_test_events.py --scenario normal
"""

import argparse
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rabbitmq_client import RabbitMQClient, load_config  # noqa: E402


def now_plus(seconds: float) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def make_event(source, source_type, event_type, zone, offset_seconds, confidence=0.9, metadata=None):
    return {
        "event_id": str(uuid.uuid4()),
        "source": source,
        "source_type": source_type,
        "event_type": event_type,
        "timestamp": now_plus(offset_seconds),
        "zone_id": zone,
        "confidence": confidence,
        "metadata": metadata or {},
    }


SCENARIOS = {
    # motion + door open, no badge -> should raise intrusion_suspected
    "intrusion": [
        make_event("camera_lobby_01", "camera", "motion_detected", "zone_lobby", 0.0),
        make_event("door_sensor_lobby_north", "sensor", "DoorOpen", "zone_lobby", 2.0),
    ],
    # repeated motion, same camera, no resolved face -> loitering_suspected
    "loitering": [
        make_event("camera_parking_03", "camera", "motion_detected", "zone_parking", 0.0),
        make_event("camera_parking_03", "camera", "motion_detected", "zone_parking", 15.0),
        make_event("camera_parking_03", "camera", "motion_detected", "zone_parking", 30.0),
    ],
    # one badge-in, multiple line crossings -> tailgating_suspected
    "tailgating": [
        make_event("badge_reader_01", "sensor", "badge_ok", "zone_entrance", 0.0, confidence=1.0),
        make_event("camera_entrance_02", "camera", "LineDetector", "zone_entrance", 1.0),
        make_event("camera_entrance_02", "camera", "LineDetector", "zone_entrance", 2.0),
        make_event("camera_entrance_02", "camera", "LineDetector", "zone_entrance", 3.0),
    ],
    # motion + door open, but WITH a badge -> should NOT raise an incident
    "normal": [
        make_event("badge_reader_01", "sensor", "badge_ok", "zone_lobby", 0.0, confidence=1.0),
        make_event("camera_lobby_01", "camera", "motion_detected", "zone_lobby", 1.0),
        make_event("door_sensor_lobby_north", "sensor", "DoorOpen", "zone_lobby", 2.0),
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), default="intrusion")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between publishes")
    args = parser.parse_args()

    config = load_config()
    client = RabbitMQClient(config)
    client.connect()
    exchange = config["exchanges"]["raw_events"]

    events = SCENARIOS[args.scenario]
    print(f"Publishing {len(events)} events for scenario '{args.scenario}'...")
    for event in events:
        routing_key = f"{event['source_type']}.{event['event_type'].lower()}"
        client.publish(exchange, routing_key, event)
        print(f"  -> published {event['event_type']} from {event['source']} (zone={event['zone_id']})")
        time.sleep(args.delay)

    client.close()
    print("Done. Check the src.main terminal for normalized events / correlated incidents.")


if __name__ == "__main__":
    main()
