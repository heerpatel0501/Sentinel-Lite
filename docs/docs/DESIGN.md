# Backend Design

## 1. Design goals

- Keep vendor complexity at the connector boundary.
- Keep HTTP concerns at the API boundary.
- Keep business workflows in services.
- Keep asynchronous work in workers.
- Keep persistence explicit and testable.

## 2. Layering

```text
Router
  ↓
Schema validation + authorization
  ↓
Service
  ↓
Repository / ORM
  ↓
PostgreSQL
```

For asynchronous flows:

```text
Connector
  ↓
Normalizer
  ↓
Message publisher
  ↓
RabbitMQ
  ↓
Worker
  ↓
Service
  ↓
PostgreSQL
```

## 3. Canonical model rules

Canonical models must be stable and vendor-neutral.

Vendor-specific attributes can be retained in a controlled metadata/raw-payload field when needed, but downstream consumers must not rely on them for core behavior.

## 4. Time handling

Store timestamps in UTC. Preserve both `occurred_at` and `received_at` where meaningful.

## 5. IDs

Use stable internal identifiers for Sentinel resources. Preserve external source identifiers separately.

## 6. Error handling

Use a consistent error envelope containing a stable machine-readable code, human-readable message and request/correlation identifier.

## 7. Idempotency

Ingestion operations must be designed so connector retries do not create duplicate cameras/events.

## 8. Transactions

State changes that need atomicity should occur in one database transaction. For database-to-message consistency, consider an outbox pattern before moving to production scale.

## 9. Async rules

No long-running AI inference, video processing, vendor polling loop or correlation scan should block a normal API request.

## 10. Logging rules

Logs must contain enough context to trace a request/event across modules. Never log plaintext VMS credentials, access tokens or sensitive evidence contents.
