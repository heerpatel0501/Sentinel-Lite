# Investigation Backend

## 1. Purpose

Provide an auditable workflow from candidate event to related data, evidence and operator verification.

## 2. Investigation object

Conceptual fields:

```text
investigation_id
case/reference number
title
status
created_by
created_at
closed_by
closed_at
summary
```

## 3. Timeline

The timeline should combine relevant events and actions in chronological order.

Possible timeline entries:

```text
event detected
AI enrichment completed
candidate generated
operator viewed
candidate verified
note added
evidence attached
investigation closed
```

## 4. Evidence

Evidence metadata should capture:

```text
evidence_id
investigation_id
event_id / camera_id when applicable
type
storage reference
captured_at
created_at
hash
created_by
```

## 5. Verification

Only authorized roles can verify/reject candidate events. Verification should generate an audit event.

## 6. Evidence integrity

Large evidence files should live outside PostgreSQL in object storage; PostgreSQL stores the authoritative metadata and integrity reference.

## 7. Access control

Investigations may be scoped to department, role or explicit case assignment depending on the operational policy adopted by the team.
