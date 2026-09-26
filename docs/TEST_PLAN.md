# Backend Test Plan

## 1. Test levels

### Unit
- normalization;
- validation;
- permission rules;
- correlation scoring/rules;
- state transitions.

### Integration
- PostgreSQL repositories;
- RabbitMQ producer/consumer;
- Redis publication;
- connector adapters;
- API + database.

### End-to-end

```text
Mock VMS
 ↓
Connector
 ↓
Normalizer
 ↓
PostgreSQL
 ↓
RabbitMQ
 ↓
Correlation
 ↓
Candidate
 ↓
Verification
 ↓
Audit
```

## 2. Critical test cases

| Area | Test |
|---|---|
| Auth | invalid credentials rejected |
| RBAC | operator cannot perform admin-only operation |
| Camera | duplicate source camera does not create duplicate record |
| Connector | one failed connector does not break other connectors |
| Event | malformed event rejected |
| Event | duplicate source event is idempotent |
| Queue | failed message retries |
| Queue | poison message reaches dead-letter handling |
| Correlation | related events produce candidate |
| Candidate | unauthorized verification rejected |
| Investigation | verified candidate can start investigation |
| Audit | verification produces audit entry |
| Realtime | authorized client receives event update |
| Health | dependency failure is reflected in readiness/health |

## 3. Acceptance test: federation

1. Start Police, Traffic and RTO mock VMS.
2. Register them.
3. Run synchronization.
4. Verify all cameras appear in a single camera query.
5. Verify each camera retains source identity.

## 4. Acceptance test: event flow

1. Trigger a mock vehicle event.
2. Verify canonical event creation.
3. Verify RabbitMQ publication.
4. Verify worker consumption.
5. Verify correlation input/output.
6. Verify realtime notification.

## 5. Acceptance test: investigation

1. Create candidate.
2. Verify candidate as authorized operator.
3. Create investigation.
4. Retrieve timeline.
5. Attach evidence metadata.
6. Verify audit history.

## 6. Performance testing

Load testing should be introduced only after the functional pipeline is stable. Test API concurrency, event throughput, queue lag and correlation processing latency separately.
