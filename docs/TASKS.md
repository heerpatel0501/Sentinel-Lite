# Tasks & Implementation Roadmap

## Phase 1: Foundation — DONE
- [x] Initialize backend (FastAPI) + frontend (React/Vite)
- [x] Configure Git, .gitignore, .env.example
- [x] SQLite dev database with auto-seed on startup
- [x] Docker Compose multi-container setup (db, backend, frontend, mediamtx)

## Phase 2: Camera Registry (Model 1) — DONE
- [x] cameras table + GIS fields (lat/long, department, vendor, status, resolution)
- [x] Seed 20 mock cameras across 5 Gujarat cities (Ahmedabad, Surat, Rajkot, Vadodara, Gandhinagar)
- [x] MapLibre GL JS map with department-colored pins
- [x] Interactive camera popup with video playback trigger

## Phase 3: VMS Federation (Model 3) — DONE
- [x] VMSProvider abstract base class with async get_stream(camera) contract
- [x] Vendor adapters: Milestone, Hikvision, Genetec, Dahua, LiveGrid
- [x] Real ONVIF adapter (ONVIFProvider) with device discovery and RTSP URL extraction
- [x] MediaMTX relay sidecar integration (internal container routing vs public browser playback)
- [x] Official Sentinel RTSP simulated-live stream adapter (SentinelOfficialRTSPAdapter)
- [x] Dynamic discovery endpoint (GET /api/ingest)
- [x] Exponential backoff reconnect policy and PTS timing synchronization

## Phase 4: AI Computer Vision Pipeline — DONE
- [x] Ultralytics YOLOv8 vehicle detection (car, 	ruck, us, motorcycle)
- [x] Dedicated license plate detector & EasyOCR character recognition
- [x] Standard Gujarat license plate normalization (GJ01-AB-1234)
- [x] Forensic evidence snapshot storage with SHA-256 integrity hash
- [x] Zero raw video storage in database (structured metadata + file URI pointers only)

## Phase 5: Database Schema & Migration — DONE
- [x] Full schema: departments, vehicle_detections, plates, watchlist, vehicle_movements (with detection_id FK), alerts, users, audit_logs, stream_health, evidence_records
- [x] SQLite runtime inspector migration in database.py (adds only missing columns, no invalid IF NOT EXISTS)
- [x] PostgreSQL PostGIS DDL (db/init.sql) in 100% parity with SQLAlchemy models
- [x] Cross-department alert seed data demonstrating correlation logic

## Phase 6: Security, RBAC & Privacy Governance — DONE
- [x] Multi-tier RBAC (dmin, nalyst, iewer) enforced server-side
- [x] Protected vehicle profile endpoint (/api/vehicle/{plate}/profile) requiring analyst/admin clearance
- [x] Viewer role restricted with HTTP 403 Forbidden
- [x] Statutory access audit logging (/api/audit-logs) aligning with DPDP Act 2023
- [x] Protected ONVIF credentials (omitted from public Camera schema)

## Phase 7: Investigator Workflow & UI — DONE
- [x] Natural language investigator search (GET /api/search?plate=...)
- [x] Chronological cross-department trajectory reconstruction
- [x] Interactive InvestigatorModal.jsx in frontend dashboard
- [x] Forensic evidence snapshot inspection card with SHA-256 verification

## Phase 8: Testing & Verification — DONE
- [x] Automated 8-test verification suite (	est_e2e_pipeline.py)
- [x] Clear separation of Local Simulated RTSP (PASS) vs Official Sandbox (BLOCKED / Credentials Required)
- [x] Frontend production build verification (
pm run build)
- [x] Docker Compose configuration validation

## Phase 9: Open-Source Hygiene & Future Enhancements
- [ ] Add LICENSE file (MIT recommended)
- [ ] Add CONTRIBUTING.md
- [ ] Bridge standalone RabbitMQ event-correlation microservice into core alerts pipeline
- [ ] Implement production user authentication (OAuth2 / JWT tokens)
