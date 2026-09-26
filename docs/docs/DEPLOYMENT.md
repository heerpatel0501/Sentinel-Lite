# Deployment Architecture — AWS

## 1. Target topology

```text
Internet
   ↓
API Gateway / NGINX
   ↓
ECS/Fargate or EC2
   ├── FastAPI
   ├── Event Worker
   └── Correlation Worker
        │
        ├── RDS PostgreSQL
        ├── ElastiCache Redis
        └── RabbitMQ
```

## 2. RDS PostgreSQL

Purpose:

- durable application data;
- camera registry;
- VMS metadata;
- events;
- candidate events;
- investigations;
- audit logs.

## 3. ElastiCache Redis

Purpose:

- realtime fanout/state;
- cache;
- rate limiting;
- short-lived coordination data.

## 4. API Gateway / NGINX

Purpose:

- public ingress;
- TLS termination as configured;
- routing;
- access/rate controls;
- request logging.

## 5. Middleware host

Run the Dockerized backend on ECS/Fargate for managed container execution, or EC2/docker-compose for a simpler hackathon deployment.

## 6. Container roles

At minimum:

```text
api
worker
correlation-worker
```

Additional connector/media/AI containers can be added when required.

## 7. Configuration

Use environment variables/secrets for:

```text
DATABASE_URL
REDIS_URL
RABBITMQ_URL
JWT_SECRET
VMS credentials references
AI service URL
```

## 8. Networking

RDS and Redis should not be publicly exposed. Only required ingress paths should be reachable from application containers.

## 9. Deployment sequence

```text
Infrastructure
 ↓
Database migrations
 ↓
Application deployment
 ↓
Workers
 ↓
Health checks
 ↓
Seed/demo data
 ↓
End-to-end smoke test
```

## 10. Hackathon priority

Prefer a working deployment over implementing every AWS service. The application should remain runnable locally through Docker Compose so cloud issues do not block development/demo preparation.
