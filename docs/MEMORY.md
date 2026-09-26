# Project Memory

## Current Status
Core dashboard, camera registry, VMS federation (mocked adapters + ONVIF + official Sentinel RTSP adapter), and real AI computer vision pipeline (YOLOv8 vehicle detection + CRAFT plate localization + EasyOCR text extraction + SHA-256 evidence generation) are fully operational and verified end-to-end. Database schema supports both PostgreSQL+PostGIS and SQLite with auto-migration. All 8 tests in 	est_e2e_pipeline.py pass cleanly.

## Completed Milestones
- **Platform Foundation**: Native execution and multi-container Docker Compose deployment.
- **Model 1 (Camera Registry)**: GIS map with MapLibre GL JS, department color-coded pins, telemetry across 5 Gujarat urban centers.
- **Model 2 (Analytics & Investigation)**: Real YOLOv8 vehicle detection, license plate localization, EasyOCR text recognition, standard Indian plate normalization (GJ01-AB-1234), forensic SHA-256 snapshots, and natural language investigator search (GET /api/search).
- **Model 3 (VMS Federation)**: Abstract VMSProvider architecture supporting Milestone, Hikvision, Genetec, Dahua, LiveGrid, ONVIF, and Sentinel Official RTSP over TCP.
- **MediaMTX Stream Relay**: Sidecar container converting RTSP streams to HLS for browser playback.
- **Database Architecture**: 11 relational tables (cameras, departments, watchlist, lerts, ehicle_detections, ehicle_movements, users, plates, udit_logs, stream_health, evidence_records).
- **Full Traceability**: detection_id foreign key in ehicle_movements linking every inter-agency sighting to its underlying AI detection and forensic keyframe crop.
- **Schema Resilience**: Runtime SQLite inspector in database.py that identifies and applies missing columns via standard ALTER TABLE without invalid IF NOT EXISTS syntax.
- **Security & RBAC**: Implemented role enforcement (dmin, nalyst, iewer), password masking in public schemas, and DPDP Act 2023 access audit logging.
- **Testing & Quality Assurance**: 8-stage automated test suite (	est_e2e_pipeline.py) with clean separation of Local Simulated RTSP vs. Official Sandbox stream status.

## Known Constraints & Operational Notes
- **Official Sentinel Sandbox Connectivity**: In local development without the sandbox WAN credentials (SENTINEL_ACCESS_PASSWORD), official sandbox requests report as BLOCKED (ReadTimeout / Credential Required). Local simulated playback operates with 100% test passing.
- **RabbitMQ Microservice**: A standalone event correlation microservice exists in the repository workspace and will be bridged into the main alerts feed in future roadmap phases.

## Next Steps
- Implement production user authentication (OAuth2 / JWT tokens).
- Maintain repository cleanliness and packaging for presentation to evaluation committees.
