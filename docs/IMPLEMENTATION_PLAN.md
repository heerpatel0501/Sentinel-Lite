# Sentinel Lite — Backend Implementation Plan

## 1. Objective

Build the Sentinel Lite backend as a vendor-neutral federation and middleware layer that can ingest camera metadata/events from multiple VMS sources, normalize them into canonical models, persist them, process events asynchronously, correlate activity across cameras, integrate AI detections, support investigation workflows, and expose a secure unified API to the frontend.

This plan is implementation-focused. It is deliberately ordered so the team gets a working vertical slice early instead of building isolated subsystems that cannot yet talk to each other.

---

## 2. Target Architecture

```text
Existing VMS / CCTV
        |
        v
VMS Connectors / Adapters
        |
        v
Canonical Normalization
        |
        +--------------------+
        |                    |
        v                    v
   PostgreSQL             RabbitMQ
        |                    |
        |                    v
        |              Event Workers
        |                    |
        |              Correlation
        |                    |
        |                   AI
        |                    |
        +---------+----------+
                  |
                  v
             Candidate Event
                  |
            Investigation
                  |
                Audit

FastAPI REST API <----> PostgreSQL
       |
       +----> Redis / realtime state
       |
       +----> WebSocket events

API Gateway / NGINX
       |
       v
FastAPI

AWS target: RDS PostgreSQL + ElastiCache Redis + ECS/Fargate or EC2.
```

---

## 3. Implementation Rules

1. Build one end-to-end path before expanding feature breadth.
2. Treat canonical schemas as contracts between team members.
3. Keep vendor-specific logic inside connectors.
4. Keep PostgreSQL as the source of truth for durable business state.
5. Use RabbitMQ for durable asynchronous event processing.
6. Use Redis for cache/realtime fanout/transient state, not as the only durable event store.
7. Keep AI behind a service/interface boundary.
8. Keep media streaming separate from business APIs.
9. Every security-sensitive action must be authorized server-side and audited.
10. Every stage must end with a runnable acceptance test or demo.

---

# 4. Phase 0 — Repository and Contracts

## Goal

Create the project skeleton and freeze the integration contracts before parallel development starts.

## Deliverables

- Backend application structure
- Environment configuration
- API versioning (`/api/v1`)
- Canonical camera schema
- Canonical event schema
- VMS schema
- Candidate-event schema
- Investigation/evidence schema
- RabbitMQ message envelope
- WebSocket event names
- Standard error response
- Authentication/RBAC model

## Exit Criteria

- All team members use the same field names and IDs.
- Frontend can mock against the API contract without waiting for backend implementation.
- Connector and AI teams know exactly what payload they must produce.

---

# 5. Phase 1 — Core Backend + PostgreSQL

## Goal

Make the backend independently runnable with persistent camera/VMS data.

## Build

- FastAPI application
- Configuration management
- PostgreSQL connection
- ORM/data-access layer
- Database migrations
- Departments
- VMS systems
- Cameras
- Basic health/readiness endpoints
- Structured logging
- API error handling

## APIs

- `GET /api/v1/health`
- `GET /api/v1/departments`
- `GET /api/v1/vms`
- `POST /api/v1/vms`
- `GET /api/v1/cameras`
- `POST /api/v1/cameras`
- `GET /api/v1/cameras/{camera_id}`
- `PATCH /api/v1/cameras/{camera_id}`
- `DELETE /api/v1/cameras/{camera_id}`

## Exit Criteria

A new camera can be inserted into PostgreSQL and retrieved through the unified API.

---

# 6. Phase 2 — VMS Federation

## Goal

Prove that different VMS sources can appear as one Sentinel system.

## Build

- `VMSConnector` interface
- Connector manager
- Mock VMS connector
- Police connector
- Traffic connector
- RTO connector
- Camera discovery
- Metadata normalization
- Source-to-Sentinel ID mapping
- Connector health monitoring
- Sync operation
- Duplicate prevention

## Canonical flow

```text
Police VMS ----\
Traffic VMS ----+--> Connector --> Normalizer --> Camera Registry
RTO VMS -------/
```

## Exit Criteria

At least three simulated VMS sources populate the same `/api/v1/cameras` registry with normalized objects.

---

# 7. Phase 3 — Authentication and RBAC

## Goal

Secure the control plane before exposing it beyond local development.

## Build

- User model
- Password hashing
- JWT access tokens
- Refresh-token strategy if required
- Roles: admin/operator/investigator
- Department scoping
- Endpoint authorization
- Secure credential references for VMS secrets
- Audit hooks for authentication and privileged actions

## Exit Criteria

A user can log in, receives a token, and cannot access resources outside their authorized role/scope.

---

# 8. Phase 4 — Event Ingestion

## Goal

Turn heterogeneous VMS events into one durable event pipeline.

## Build

- Canonical event model
- Event API for controlled/manual ingestion
- Connector event ingestion
- Event validation
- `occurred_at` vs `received_at`
- Source event IDs
- Idempotency/deduplication
- PostgreSQL persistence
- RabbitMQ producer
- Retry policy
- Dead-letter handling

## Flow

```text
VMS
 |
v
Connector
 |
v
Canonical Event
 |
v
Validate + Deduplicate
 |
+-------> PostgreSQL
 |
v
RabbitMQ
```

## Exit Criteria

The same source event can be retried without producing duplicate logical events, and failed processing is recoverable.

---

# 9. Phase 5 — Realtime Layer

## Goal

Push state changes to connected dashboards without polling for every update.

## Build

- Redis connection
- Event/status channels
- WebSocket manager
- Event broadcasting
- Camera-health broadcasting
- Candidate-event broadcasting
- Connection authentication
- Reconnect-safe behavior

## Example realtime events

- `camera.status_changed`
- `event.created`
- `event.updated`
- `candidate.created`
- `candidate.verified`
- `investigation.updated`

## Exit Criteria

A backend event causes a connected client to receive a realtime notification without another REST request.

---

# 10. Phase 6 — Cross-Camera Correlation

## Goal

Transform isolated events into meaningful candidate events.

## Build

- Camera relationships
- Spatial proximity checks
- Time-window logic
- Event-type compatibility rules
- Vehicle/person attribute matching when available
- Correlation scoring
- Related-event grouping
- Candidate-event creation
- Candidate state machine

## State model

```text
CREATED
   |
   v
PROCESSING
   |
   v
CANDIDATE
   |
   v
UNDER_REVIEW
   |       |
   v       v
VERIFIED  REJECTED
```

## Exit Criteria

A sequence of events from multiple cameras can produce one candidate event containing related event IDs, cameras and a reproducible correlation score.

---

# 11. Phase 7 — AI Integration

## Goal

Add AI assistance without coupling the core backend to a particular ML framework.

## Build

- AI request contract
- AI result contract
- AI service adapter
- Vehicle detection integration
- Person detection integration where available
- Plate/OCR integration only if feasible
- Detection confidence storage
- Correlation-confidence separation
- AI timeout/retry handling

## Flow

```text
Event / Frame Reference
        |
        v
     AI Service
        |
        v
Detections + confidence
        |
        v
Canonical Event / Candidate
```

## Exit Criteria

The backend can accept a model result from the AI service and attach it to the corresponding event without depending on the AI implementation details.

---

# 12. Phase 8 — Investigation and Evidence

## Goal

Provide the complete investigation backend behind the operator workflow.

## Build

- Investigation entity
- Candidate-to-investigation relationship
- Related cameras
- Related events
- Timeline generation
- Evidence metadata
- Evidence provenance
- Evidence hashing
- Verification actions
- Investigator notes/status
- Audit trail

## Exit Criteria

An investigator can open a candidate, view the related timeline/cameras/events, attach evidence, verify/reject the candidate, and leave an auditable history.

---

# 13. Phase 9 — Dashboard Aggregation APIs

## Goal

Provide frontend-ready responses without requiring the UI to understand internal architecture.

## Build

- Dashboard summary
- Camera statistics
- VMS health summary
- Recent events
- Active candidate summary
- Department summary
- Recent system activity

## Key API

`GET /api/v1/dashboard/summary`

## Exit Criteria

The frontend can build the main dashboard with a small number of backend calls and does not need to query RabbitMQ/PostgreSQL/Redis directly.

---

# 14. Phase 10 — Media Control Plane

## Goal

Expose secure stream/session metadata while keeping media delivery outside the core API process.

## Build

- Camera stream metadata
- Stream capability model
- Authorized stream-session creation
- Media gateway integration contract
- Expiring stream/session references

## Boundary

```text
FastAPI = control plane
Media gateway = video plane
```

## Exit Criteria

The frontend can request an authorized stream/session reference without receiving raw VMS credentials.

---

# 15. Phase 11 — Production Hardening

## Build

- Rate limiting
- Secure headers
- CORS rules
- Secret management
- Database connection pooling
- Request IDs
- Correlation IDs
- Structured JSON logs
- Metrics
- Liveness/readiness checks
- Dependency health checks
- Retries/backoff
- Outbox pattern where message/database consistency requires it
- Idempotency keys
- Dead-letter queues
- Backup/restore procedures

## Exit Criteria

The backend can survive normal dependency failures without taking down unrelated components, and failures are observable.

---

# 16. Phase 12 — Docker and AWS Deployment

## Target

```text
API Gateway / NGINX
        |
        v
ECS/Fargate or EC2
        |
        +---- FastAPI
        +---- Event Worker
        +---- Correlation Worker
        |
        +---- RDS PostgreSQL
        +---- ElastiCache Redis
        +---- RabbitMQ
```

## Build

- Production Docker images
- Environment-specific configuration
- RDS connection
- ElastiCache connection
- RabbitMQ deployment/connection
- ECS/Fargate or EC2 deployment
- Secrets management
- TLS
- Logging and monitoring
- Health checks
- CI/CD pipeline

## Exit Criteria

A clean deployment can start all required services, reach RDS/Redis/RabbitMQ, expose the API, and pass smoke tests.

---

# 17. Phase 13 — End-to-End Demo Validation

## Demo scenario

```text
Police VMS
Traffic VMS
RTO VMS
   |
   v
Sentinel connectors
   |
   v
Unified camera registry
   |
   v
Vehicle event
   |
   v
RabbitMQ
   |
   v
Correlation
   |
   v
Candidate event
   |
   v
AI confidence / attributes
   |
   v
Operator verification
   |
   v
Investigation
   |
   v
Audit log
   |
   v
Realtime dashboard update
```

## Exit Criteria

The team can run one uninterrupted story from federated VMS input to operator investigation without manually editing database rows or bypassing backend services.

---

# 18. Parallel Team Work

## Backend / Middleware

Own:

- FastAPI
- canonical contracts
- orchestration
- API gateway boundary
- VMS connector abstraction
- auth/RBAC
- database integration
- service integration

## VMS Integration

Own:

- ONVIF
- RTSP
- vendor APIs
- mock VMS sources
- vendor-specific normalization inputs

## Event / Correlation

Own:

- event workers
- RabbitMQ
- correlation rules
- candidate generation

## Frontend / GIS

Consume:

- `/api/v1/cameras`
- `/api/v1/events`
- `/api/v1/candidates`
- `/api/v1/investigations`
- `/api/v1/dashboard/summary`
- WebSocket events

## AWS / DevOps

Own:

- RDS
- ElastiCache
- RabbitMQ infrastructure
- Docker
- ECS/Fargate or EC2
- monitoring/logging
- secrets/networking

## AI / Analytics

Own:

- inference
- detections
- OCR if feasible
- AI result contract
- model serving

---

# 19. Recommended Build Order for a Hackathon

Do not attempt all phases at once.

### Milestone A — Working federation

```text
3 mock VMS
   ↓
3 connectors
   ↓
normalization
   ↓
PostgreSQL
   ↓
unified camera API
```

### Milestone B — Working events

```text
VMS event
   ↓
normalize
   ↓
RabbitMQ
   ↓
worker
   ↓
PostgreSQL
```

### Milestone C — Working intelligence

```text
events
   ↓
correlation
   ↓
candidate
   ↓
AI enrichment
```

### Milestone D — Working investigation

```text
candidate
   ↓
timeline
   ↓
evidence
   ↓
verification
   ↓
audit
```

### Milestone E — Working cloud deployment

```text
Gateway
   ↓
FastAPI
   ↓
RDS / Redis / RabbitMQ
```

---

# 20. Definition of Done

The backend is considered ready for the hackathon demo when:

- [ ] 3+ VMS sources can be represented through the federation layer.
- [ ] All camera data is exposed through one canonical API.
- [ ] Camera status is tracked.
- [ ] Events use a canonical schema.
- [ ] Duplicate source events are safely handled.
- [ ] RabbitMQ processing works end-to-end.
- [ ] Correlation produces candidate events.
- [ ] Candidate confidence is reproducible from stored inputs.
- [ ] AI results can enrich events/candidates.
- [ ] Operators can verify/reject candidates.
- [ ] Investigations expose related cameras/events/timeline.
- [ ] Evidence metadata is recorded with provenance.
- [ ] Security and role checks are enforced server-side.
- [ ] Important actions generate audit logs.
- [ ] Realtime updates reach connected clients.
- [ ] Dashboard aggregation endpoints work.
- [ ] Backend runs in Docker.
- [ ] Cloud deployment path is documented and tested.
- [ ] End-to-end demo can run without manual database manipulation.
