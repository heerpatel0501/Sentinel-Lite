# Event Processing Pipeline (ADR-003: Redis Unified Messaging)

## 1. Purpose

Turn heterogeneous VMS/AI events into a durable, traceable, asynchronous processing pipeline using Redis as the unified messaging layer per ADR-003 (RabbitMQ is retired).

## 2. Event Flow

```text
Event Producer (VMS / Camera / Sensor)
      ↓
Event Normalization (src/normalizer.py)
      ↓
Redis Unified Messaging Layer
      ┌───────────────────────────┴───────────────────────────┐
      ↓                                                       ↓
Redis List Queue (`sentinel:queue`)             Redis Pub/Sub (`sentinel:events`)
      ↓                                                       ↓
Event Worker (`backend/event_worker.py`)         WebSocket Bridge (`backend/main.py`)
      ↓                                                       ↓
Correlation Engine (`src/correlation_engine.py`) Command Center Dashboards (/ws)
      ↓
Candidate Correlated Event / State Alert
      ↓
API Fanout & PostgreSQL Persistence
```

Failed events move after max retries (3 attempts) to:
```text
sentinel:queue:dlq (Dead-Letter Queue with failure metadata)
```

## 3. Redis Channels & Queues

Per ADR-003, Redis (ElastiCache / Redis 7) serves as the unified event broker:

- **`sentinel:events`** (Pub/Sub): Immediate broadcast to WebSocket consumers, dashboard updates, and candidate event notifications.
- **`sentinel:queue`** (List Queue): Durable worker queue consumed via `LPOP` / `BRPOP` for asynchronous event correlation and AI enrichment.
- **`sentinel:queue:dlq`** (List Queue): Dead-Letter Queue capturing messages that fail after bounded retries, retaining `_dead_lettered_at`, `_retry_count`, and `_error`.

## 4. Message Envelope

Canonical event message envelope:

```json
{
  "event_id": "EVT-001",
  "source_id": "CAM-001",
  "camera_id": "AHM-Junction-01",
  "event_type": "vehicle_detection",
  "occurred_at": "2026-09-28T14:00:00Z",
  "confidence": 0.95,
  "payload": {
    "plate": "GJ01-AB-1234",
    "department": "Police",
    "vehicle_type": "car"
  }
}
```

## 5. Idempotency & Bounded Retries

- Consumers are idempotent: deduplicated via `source_id` / `event_id`.
- Handlers execute with exponential backoff (`min(0.05 * 2^retry, 5.0)`).
- When retries reach `max_retries` (3), the event is shifted to `sentinel:queue:dlq`.

## 6. Correlation Engine Rules

The sliding-window correlation engine (`src/correlation_engine.py`) evaluates:
1. **Intrusion**: Motion detected + entry event in the same zone without badge-in.
2. **Loitering**: Multiple motion events from the same camera without face resolution.
3. **Tailgating**: Multiple line crossings following a single access grant.
4. **Multi-Camera Motion**: Sequential motion detected across $\ge 2$ distinct cameras within the time window.
5. **Cross-Department Plate Sightings**: Target plate detected across $\ge 2$ distinct departments (e.g. Police and RTO) within the correlation window.
