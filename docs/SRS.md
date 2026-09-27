# Software Requirements Specification — Sentinel Lite Backend

## 1. Functional requirements

### FR-01 Authentication
The system shall authenticate users and issue short-lived access tokens with an appropriate refresh mechanism.

### FR-02 Authorization
The system shall enforce role-based access control and resource/department scope.

### FR-03 VMS registration
Authorized users shall be able to create, view, update and disable VMS source definitions.

### FR-04 Connector lifecycle
The system shall expose connector health, connection state and synchronization actions.

### FR-05 Camera federation
The system shall discover or ingest camera metadata from connectors and normalize it into the Sentinel camera schema.

### FR-06 Camera registry
The system shall persist a unique Sentinel camera identity while retaining the originating VMS and external camera identity.

### FR-07 Camera health
The system shall maintain current camera health and last-seen information.

### FR-08 Event ingestion
The system shall accept normalized events and validate schema, timestamp, source identity and required fields.

### FR-09 Event idempotency
The system shall prevent duplicate persistence of the same source event where a stable source event identity exists.

### FR-10 Event processing
The system shall publish processable events to the asynchronous event pipeline.

### FR-11 Retry and dead-letter handling
Failed asynchronous processing shall be retried according to policy and ultimately routed to a dead-letter path when recovery is not possible.

### FR-12 Correlation
The system shall correlate events using configurable temporal, spatial and metadata relationships.

### FR-13 Candidate events
The system shall create candidate events containing related event references, confidence and current review state.

### FR-14 Operator verification
Authorized users shall be able to verify or reject candidate events.

### FR-15 AI integration
The system shall accept structured AI detection results without coupling the API process to a specific model implementation.

### FR-16 Investigation
The system shall support investigation creation, related event association, timeline retrieval, evidence metadata and closure.

### FR-17 Audit logging
Security and workflow actions shall be recorded with actor, timestamp, action and resource context.

### FR-18 Realtime updates
The system shall deliver selected state changes to connected clients through realtime messaging.

### FR-19 Dashboard aggregation
The system shall provide backend-composed summary endpoints for camera, event, VMS and candidate status.

### FR-20 Health endpoints
The system shall provide application liveness, readiness and dependency health information.

## 2. Non-functional requirements

### NFR-01 Reliability
A failure in one connector or worker shall not take down unrelated connectors or the API.

### NFR-02 Scalability
The API and asynchronous workers shall be independently scalable.

### NFR-03 Security
Credentials shall not be exposed through ordinary resource APIs; privileged operations require authorization.

### NFR-04 Observability
Requests, worker operations and connector failures shall be diagnosable using structured logs and request/correlation identifiers.

### NFR-05 Maintainability
Domain logic shall be separated from API routing, persistence and infrastructure adapters.

### NFR-06 Interoperability
Connector-specific payloads shall be normalized before entering the common application domain.

### NFR-07 Performance
Heavy AI/video processing shall not run synchronously inside latency-sensitive API requests.

### NFR-08 Auditability
Important state-changing operations shall be attributable to an actor or service identity.

## 3. Requirement priority

| Priority | Meaning |
|---|---|
| P0 | Required for core demonstration |
| P1 | Required for complete MVP |
| P2 | Valuable extension |

P0: authentication, cameras, VMS federation, events, RabbitMQ pipeline, correlation, unified API, health.  
P1: AI contract, investigation, audit, realtime, evidence metadata, deployment.  
P2: advanced analytics, deeper vendor coverage, stronger HA and scaling.
