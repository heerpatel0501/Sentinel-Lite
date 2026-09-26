# Product Requirements Document — Sentinel Lite Backend

## 1. Product overview

**Sentinel Lite** is the middleware/federation backend for Model 3 of the CCTV Integration Hackathon 2026.

The backend connects heterogeneous departmental CCTV/VMS systems without replacing them. It normalizes vendor-specific metadata and events into a canonical model, exposes unified APIs, processes events asynchronously, correlates activity across cameras, supports AI-assisted analytics, and provides investigation/audit capabilities to downstream operator applications.

## 2. Problem

Different departments may operate different VMS, camera vendors, NVRs and APIs. A downstream operator should not need to integrate separately with every vendor.

## 3. Product goal

Create one backend boundary through which downstream systems can:

- discover and query federated cameras;
- understand camera health and ownership;
- consume standardized events;
- receive candidate cross-camera events;
- conduct investigations;
- verify operator decisions;
- access evidence metadata;
- retrieve auditable history.

## 4. Target users

| User | Backend needs |
|---|---|
| Administrator | Manage users, departments, VMS systems, configuration |
| Operator | View cameras/events, acknowledge and verify candidates |
| Investigator | Search events, open investigations, review evidence |
| Integration service | Register/connect VMS and submit normalized data |
| AI service | Submit/receive structured detection results |
| Frontend/dashboard | Consume REST + realtime APIs |

## 5. Core product capabilities

### Federation
Connect existing VMS through connector abstractions for ONVIF, RTSP and vendor APIs.

### Canonical models
Normalize vendor-specific camera metadata and events into stable Sentinel schemas.

### Unified API
Provide one versioned API for downstream applications.

### Event processing
Accept events, validate and deduplicate them, publish them for asynchronous processing, and persist the authoritative event record.

### Correlation
Group related events across cameras/time windows and produce candidate events with explainable correlation evidence.

### AI orchestration
Allow AI services to add structured detections and model confidence to events.

### Investigation
Turn verified/candidate activity into an investigator workflow containing related events, cameras, timeline, evidence and audit history.

### Auditability
Record security-sensitive and workflow-sensitive actions.

### Realtime updates
Publish operational changes to connected dashboards through a realtime channel.

## 6. MVP

The first working vertical slice is:

```text
3 Mock VMS
  ↓
3 Connectors
  ↓
Canonical Camera Model
  ↓
PostgreSQL
  ↓
Unified Camera API
  ↓
Frontend
```

Then:

```text
Events
  ↓
RabbitMQ
  ↓
Correlation
  ↓
AI
  ↓
Investigation
```

## 7. Success criteria

The backend is considered MVP-ready when it can:

1. register at least three VMS sources;
2. normalize their camera metadata into one schema;
3. store cameras in PostgreSQL;
4. expose all cameras through one API;
5. ingest normalized events;
6. process events through an asynchronous queue;
7. prevent duplicate event creation;
8. generate a candidate event from related events;
9. verify/reject the candidate through an authorized API;
10. produce an auditable investigation trail;
11. expose realtime updates to the dashboard;
12. run locally through Docker and be deployable to AWS infrastructure.

## 8. Out of scope for the first hackathon MVP

- replacing existing VMS platforms;
- building a full commercial VMS;
- implementing every vendor's private API;
- developing a custom computer-vision foundation model;
- full enterprise-scale multi-region disaster recovery;
- production-grade video transcoding from scratch.

## 9. Product principles

- **Vendor-neutral:** downstream clients should not depend on vendor-specific payloads.
- **Observable:** failures must be visible.
- **Auditable:** important operator/system actions must be attributable.
- **Asynchronous where appropriate:** heavy processing must not block API requests.
- **Data lineage:** preserve source identifiers and provenance.
- **Secure by default:** credentials and privileged operations must be protected.
- **Incremental:** a working vertical slice has priority over theoretical completeness.
