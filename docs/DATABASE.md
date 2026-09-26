# Database Design — PostgreSQL / RDS

## 1. Persistence principle

PostgreSQL is the authoritative store for durable business state.

## 2. Core entities

```text
users
roles / role assignments
 departments
vms_systems
cameras
camera_health_history
events
candidate_events
candidate_event_items
investigations
evidence
audit_logs
```

## 3. Relationships

```text
department ──< users
department ──< vms_systems
vms_system ──< cameras
camera ──< events
event ──< candidate_event_items
candidate_event ──< investigations
investigation ──< evidence
user ──< audit_logs
```

## 4. Camera identity

A camera record should retain both:

- Sentinel internal ID;
- source VMS ID.

A unique constraint should prevent accidental duplicate source mappings inside the same VMS.

## 5. Event identity

Where the source provides a stable event ID, store it with the source/VMS identity and use it for idempotency.

## 6. Candidate event

The candidate record should contain its current state and aggregate confidence, while related event references should remain queryable rather than embedded as an opaque blob only.

## 7. Investigation

An investigation links operational/candidate findings to a workflow. It should preserve creation/closure timestamps and actor identity.

## 8. Evidence

Store metadata and provenance in PostgreSQL; large media should be stored in object storage with a stable reference and integrity hash.

## 9. Index strategy

Prioritize indexes around:

```text
events(camera_id, occurred_at)
events(event_type, occurred_at)
events(status, occurred_at)
cameras(department_id)
cameras(status)
candidate_events(status, created_at)
audit_logs(user_id, created_at)
```

Exact indexes should be confirmed against real query plans.

## 10. Data retention

Retention periods must be configurable. The project source does not define a final retention policy, so it should not be hard-coded as a requirement.

## 11. Migrations

Schema changes should be migration-driven. Avoid manual production schema edits.
