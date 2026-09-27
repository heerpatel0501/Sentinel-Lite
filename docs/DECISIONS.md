# Architecture Decisions

## ADR-001: FastAPI for the core backend
**Status:** Accepted

FastAPI is selected as the primary backend framework because the project already identifies Python/FastAPI as a candidate and the AI integration naturally benefits from Python interoperability.

## ADR-002: PostgreSQL as system of record
**Status:** Accepted

The project explicitly identifies PostgreSQL for structured application state. AWS RDS is the managed deployment target proposed by the team.

## ADR-003: Redis for real-time events and worker queuing (Supersedes RabbitMQ)
**Status:** Accepted (Locked in Architecture Step 1)

Redis (ElastiCache / Redis 7) is locked as the unified real-time event and messaging layer. RabbitMQ is retired to eliminate dual-broker operational complexity. Redis Pub/Sub provides immediate fanout to WebSockets and dashboards, while Redis list queues handle background asynchronous task execution with DLQ support.

## ADR-004: Redis for realtime/cache; PostgreSQL for persistent record
**Status:** Accepted (Locked in Architecture Step 1)

PostgreSQL remains the permanent, authoritative system of record for investigations, vehicle detections, OCR plates, evidence records (SHA-256 hashes), and audit logs. Redis is strictly the ephemeral real-time layer and does not replace PostgreSQL.


## ADR-005: Modular monolith + workers
**Status:** Accepted

Keep the main backend as a modular FastAPI application and separate long-running processing into workers. This reduces deployment complexity while preserving domain boundaries.

## ADR-006: Canonical model at connector boundary
**Status:** Accepted

Vendor-specific payloads are translated before they enter the core domain to protect downstream consumers from vendor coupling.

## ADR-007: Versioned API
**Status:** Accepted

All external application endpoints start at `/api/v1` to make future changes manageable.

## ADR-008: Three mock VMS for MVP
**Status:** Accepted

Three simulated sources provide a deterministic demonstration of federation before real vendor integrations are completed.

## ADR-009: AI as replaceable service
**Status:** Accepted

AI inference stays behind a contract so model/framework changes do not require a rewrite of the backend.

## Pending decisions

- Exact AWS ingress choice: Locked (AWS Application Load Balancer / ALB selected; API Gateway explicitly excluded).
- Event broker hosting: Locked (AWS ElastiCache Redis selected; RabbitMQ retired).
- Object storage provider/bucket policy for evidence.
- Long-term retention periods.
- Final ONVIF/vendor coverage.
- Production HA/backup policy.
