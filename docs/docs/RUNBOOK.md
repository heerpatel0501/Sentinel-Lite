# Backend Operations Runbook

## 1. Start locally

```bash
docker compose up --build
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

## 2. Health diagnosis

Check application health first, then dependencies:

```text
API
 ↓
PostgreSQL
 ↓
RabbitMQ
 ↓
Redis
 ↓
VMS connectors
 ↓
AI service
```

## 3. VMS connector failure

Symptoms:
- VMS unavailable;
- camera data stale;
- connector health degraded.

Actions:
1. check connector logs;
2. check source endpoint/network;
3. verify credentials reference;
4. retry synchronization;
5. confirm unrelated connectors remain healthy.

## 4. Event backlog

Check:
- RabbitMQ queue depth;
- worker health;
- database latency;
- malformed-message/dead-letter volume.

Do not simply restart workers repeatedly without identifying why messages fail.

## 5. Database issue

Check:
- connection pool;
- RDS availability;
- migration status;
- slow queries;
- disk/storage thresholds.

## 6. Redis issue

The system should continue to preserve durable business state in PostgreSQL even if realtime/cache functionality degrades. Restore Redis and reconnect subscribers/clients.

## 7. Candidate anomaly

When a candidate looks wrong:

1. inspect the candidate;
2. inspect related events;
3. inspect timestamps and camera relationships;
4. inspect AI enrichment;
5. inspect correlation logs;
6. verify/reject through authorized workflow;
7. retain audit trail.

## 8. Security incident

Immediately preserve logs and audit records, revoke compromised credentials/tokens, isolate affected integration if required, and rotate secrets through the configured secret-management process.
