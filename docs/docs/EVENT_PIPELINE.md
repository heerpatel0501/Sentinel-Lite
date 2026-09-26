# Event Processing Pipeline

## 1. Purpose

Turn heterogeneous VMS/AI events into a durable, traceable, asynchronous processing pipeline.

## 2. Flow

```text
VMS
 ↓
Connector
 ↓
Normalization
 ↓
Validation + deduplication
 ↓
PostgreSQL event record
 ↓
RabbitMQ
 ↓
Processing worker
 ↓
Correlation / AI
 ↓
Candidate event
 ↓
Realtime notification
```

## 3. RabbitMQ responsibilities

Use RabbitMQ for work that should survive consumer restart and be retried.

Logical event categories may include:

```text
raw
normalized
ai
correlation
candidate
```

Actual exchange/queue names can be versioned as the implementation evolves.

## 4. Message envelope

A common message envelope should include:

```json
{
  "message_id": "MSG-001",
  "event_type": "vehicle_detected",
  "occurred_at": "2026-09-26T13:00:00Z",
  "source": {
    "vms_id": "VMS-01",
    "camera_id": "CAM-001"
  },
  "payload": {}
}
```

## 5. Idempotency

Consumers must be safe under message redelivery.

## 6. Retry

Use bounded retries with backoff. Messages that repeatedly fail should move to a dead-letter mechanism for inspection.

## 7. Outbox consideration

If production reliability requires guaranteed database-to-message publication, an outbox table/worker should be added so DB persistence and publication intent are atomic.

## 8. Redis role

Redis/ElastiCache can be used for:

- realtime fanout;
- cache;
- short-lived state;
- rate limiting.

It should not silently replace RabbitMQ's durable processing responsibility unless the team intentionally changes the architecture and updates this contract.
