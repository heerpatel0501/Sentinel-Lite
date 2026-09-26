# Sentinel Lite Backend Memory

## Project identity

Sentinel Lite is a vendor-neutral VMS federation and middleware platform for the Model 3 CCTV Integration Hackathon architecture.

## Core proposition

Federate existing CCTV/VMS infrastructure instead of replacing it.

## Existing systems

The conceptual environment includes Police, Traffic, RTO and Municipal VMS sources.

## Canonical objects

The two most important common models are:

```text
Camera
Event
```

## Event flow

```text
VMS
 → Connector
 → Normalizer
 → RabbitMQ
 → Correlation
 → AI
 → Candidate Event
 → Operator Verification
 → Investigation / Audit
```

## Cloud infrastructure

Current proposed infrastructure:

```text
RDS PostgreSQL
ElastiCache Redis
API Gateway / NGINX
ECS/Fargate or EC2
```

## Important distinction

- PostgreSQL = durable source of truth.
- RabbitMQ = durable asynchronous processing.
- Redis = cache/realtime/transient exchange.
- FastAPI = core middleware/API.

## Current backend codebase

The repository uses a modular FastAPI application, PostgreSQL models/schemas, connectors, RabbitMQ/event handling, AI schemas/service, investigations, authentication, realtime and Docker support.

## Product demo story

Show heterogeneous VMS → connect them → normalize → unified camera registry → event → processing → correlation → candidate → investigation/audit.

## Things not to invent

Do not claim full vendor compatibility, production-scale throughput, AI accuracy, government deployment, or security certification unless separately verified.
