# Backend Implementation Plan

## Milestone 0 — Contracts — DONE
- [x] Freeze camera schema
- [x] Freeze VMS schema
- [x] Freeze event schema
- [x] Freeze candidate state machine
- [x] Freeze investigation object
- [x] Freeze REST endpoints (/api/v1)
- [x] Freeze message envelope
- [x] Freeze realtime event names

## Milestone 1 — Core backend — DONE
- [x] FastAPI application setup
- [x] configuration and environment loading
- [x] PostgreSQL connection + SQLite fallback
- [x] migrations & schema compatibility
- [x] departments
- [x] users
- [x] authentication (HMAC-SHA256 JWT)
- [x] RBAC (Admin, Analyst, Viewer)
- [x] health/readiness endpoints

## Milestone 2 — Federation — DONE
- [x] VMS CRUD (/api/v1/vms)
- [x] connector interface (VMSProvider)
- [x] mock Police connector (Milestone)
- [x] mock Traffic connector (Hikvision)
- [x] mock RTO connector (Genetec/Dahua)
- [x] normalization service
- [x] camera registry (/api/v1/cameras)
- [x] connector health
- [x] camera health

## Milestone 3 — Events — DONE
- [x] event schema (CanonicalEvent)
- [x] event ingestion API (POST /api/v1/events)
- [x] idempotency & deduplication (source_id)
- [x] event persistence
- [x] cross-service event bridge (POST /api/events/correlate)

## Milestone 4 — Correlation — DONE
- [x] camera relationship model
- [x] time-window correlation
- [x] related-event grouping
- [x] candidate event creation (GET /api/v1/candidates)
- [x] verify/reject APIs (POST /api/v1/candidates/{id}/verify, reject)

## Milestone 5 — AI — DONE
- [x] AI request schema
- [x] AI result schema
- [x] AI service adapter (SentinelAIEngine)
- [x] vehicle detection (YOLOv8)
- [x] license plate localization (CRAFT neural text ROI)
- [x] plate/OCR integration (EasyOCR + Gujarat regex normalization)
- [x] cryptographic evidence crop & SHA-256 integrity hashing

## Milestone 6 — Investigation — DONE
- [x] investigation CRUD (/api/v1/investigations)
- [x] timeline aggregation (/api/v1/investigations/{id}/timeline)
- [x] evidence metadata (/api/v1/investigations/{id}/evidence)
- [x] integrity hash fields (SHA-256)
- [x] audit integration (audit_logs & DPDP Act compliance)

## Milestone 7 — Realtime — DONE
- [x] WebSocket manager (ConnectionManager)
- [x] event broadcasting (/ws and /api/v1/ws)
- [x] camera health updates
- [x] candidate updates (candidate.verified, candidate.rejected)

## Milestone 8 — Deployment — DONE
- [x] Docker image (backend, frontend)
- [x] Docker Compose local stack (db, backend, frontend, mediamtx)
- [x] MediaMTX RTSP-to-HLS relay sidecar
- [x] smoke test & E2E verification

## Milestone 9 — Hardening — DONE
- [x] 8-stage automated test suite (test_e2e_pipeline.py)
- [x] frontend production build validation (npm run build)
- [x] structured audit trails
- [x] AWS cloud formation / ECS deployment automation (deploy/aws/)
- [x] load testing under 100+ concurrent RTSP channels & API queries (test_load_concurrency.py)

## Milestone 10 — Production Hardening (Phase 11) — DONE
- [x] Rate limiting middleware (sliding window, 300 RPM + 60 burst/sec)
- [x] Security headers (OWASP: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS, Cache-Control)
- [x] Request ID injection (X-Request-ID, client passthrough or auto-generated UUID)
- [x] Structured JSON access logging (timestamp, method, path, status, duration, client, request_id)
- [x] Application metrics endpoint (/metrics — request counts, latency, error rates, top endpoints)
- [x] Readiness probe (/ready — database connectivity + schema check for K8s/ECS)
- [x] Event worker queue (RabbitMQ production / in-memory dev fallback)
- [x] Dead-letter queue (DLQ) for failed event processing
- [x] Exponential backoff retry on event processing failures
- [x] Event queue stats endpoint (GET /api/v1/queue/stats)
- [x] CORS rules (allow_origins configurable)
- [x] Database connection pooling (50 pool + 50 overflow)
- [x] Idempotency keys (source_id deduplication on event ingestion)

## Milestone 11 — CI/CD Pipeline — IN PROGRESS
- [x] GitHub Actions workflow (lint, test, build, deploy)
- [ ] Terraform infrastructure-as-code
- [ ] Staging environment configuration
