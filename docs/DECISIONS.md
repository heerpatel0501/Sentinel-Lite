# Architecture Decisions

## ADR-001: FastAPI for the core backend
**Status:** Accepted

FastAPI is selected as the primary backend framework because the project already identifies Python/FastAPI as a candidate and the AI integration naturally benefits from Python interoperability.

## ADR-002: PostgreSQL as system of record
**Status:** Accepted

The project explicitly identifies PostgreSQL for structured application state. AWS RDS is the managed deployment target proposed by the team.

## ADR-003: RabbitMQ for durable event processing
**Status:** Accepted

The project defines RabbitMQ as the event-bus concept for normalized event processing and correlation.

## ADR-004: Redis for realtime/cache responsibilities
**Status:** Accepted

Redis/ElastiCache is used for cache and realtime fanout/transient state. It does not automatically replace RabbitMQ for durable worker processing.

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

- Exact AWS ingress choice: API Gateway vs NGINX/ALB combination.
- Exact RabbitMQ hosting option.
- Object storage provider/bucket policy for evidence.
- Long-term retention periods.
- Final ONVIF/vendor coverage.
- Production HA/backup policy.
