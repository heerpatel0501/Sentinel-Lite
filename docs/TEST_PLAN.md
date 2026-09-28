# Comprehensive Test Plan

## 1. Overview & Test Objectives
This document establishes the end-to-end verification strategy for **Sentinel-Lite**. It outlines automated test suites, stream protocol validations, computer vision accuracy benchmarks, security enforcement, and regression test suites required for the **I-Hub Gujarat Sentinel CCTV Hackathon** evaluation.

---

## 2. Automated Test Suite (test_e2e_pipeline.py)

The automated test suite contains **exactly 8 numbered test stages**, verifying every layer from raw RTSP packet decoding to the investigator user interface:

| Stage | Test Name | Key Assertions |
|-------|-----------|----------------|
| **[TEST 1/8]** | **Database Schema & Resilient Migration** | 1. Verified all 11 tables exist in active database engine.<br>2. Verified cameras table contains ONVIF connection columns (onvif_host, onvif_port, onvif_username, onvif_password).<br>3. Verified vehicle_movements contains detection_id foreign key for evidence traceability.<br>4. Verified public Camera schema explicitly omits onvif_password to protect credentials. |
| **[TEST 2/8]** | **Dynamic Ingestion Catalogue (/api/ingest)** | 1. Discovery returns HTTP 200 with dynamic stream endpoints.<br>2. Verified transport is strictly **RTSP over TCP** (interleaved framing).<br>3. Verified synchronization mode is container **Presentation Time Stamp (PTS)**.<br>4. Verified support for mixed H.264 and H.265 video codecs. |
| **[TEST 3/8]** | **Full Computer Vision AI Pipeline** | 1. Ingests video frame and executes Ultralytics YOLOv8 vehicle detection.<br>2. Extracts high-confidence license plate ROI.<br>3. Runs EasyOCR character recognition on localized crop.<br>4. Normalizes plate syntax into standard Gujarat format (GJ01-AB-1234).<br>5. Generates forensic keyframe crop on disk and calculates 64-character **SHA-256** hash.<br>6. Persists detection, plate, and evidence records with valid relational linking. |
| **[TEST 4/8]** | **Investigator Natural Language Search (/api/search)** | 1. Parses natural language string (e.g. 'Locate suspect vehicle GJ01-AB-1234 near SG Highway').<br>2. Extracts normalized target plate GJ01-AB-1234.<br>3. Matches state-wide stolen watchlist registry.<br>4. Reconstructs chronological multi-department journey trajectory.<br>5. Verifies valid URI reference pointers to photographic evidence snapshots. |
| **[TEST 5/8]** | **RBAC Clearance & Privacy Audit Governance** | 1. Request with X-User-Role: analyst accesses /api/vehicle/{plate}/profile -> **HTTP 200** with synthetic VAHAN registry data.<br>2. Request with X-User-Role: viewer is restricted with **HTTP 403 Forbidden**.<br>3. Verifies statutory access audit entry recorded in audit_logs table. |
| **[TEST 6/8]** | **Stream Telemetry & Health Monitoring (/api/streams/health)** | 1. Queries real-time telemetry across monitored camera channels.<br>2. Verifies channel metrics: active status, H.264/H.265 codec, resolution, FPS, and container PTS timestamps. |
| **[TEST 7/8]** | **VMS Adapter Async Contract & MediaMTX Networking** | 1. Verifies all 8 VMS providers implement async def get_stream(camera) without TypeError.<br>2. Tests MediaMTX relay host path (http://localhost:8888) and internal Docker path (http://mediamtx:8888). |
| **[TEST 8/8]** | **RTSP Stream Status (Separated Reporting)** | 1. **Local Simulated Stream**: Decodes test video/synthetic frames, verifies PTS timing -> **PASS**.<br>2. **Official Sentinel Sandbox RTSP**: Probes sandbox network and credentials (SENTINEL_ACCESS_PASSWORD). If credentials/network are unreachable from the test environment, explicitly reports **BLOCKED** with clear rationale. |

---

## 3. Frontend Build & Static Validation
- **Command**: cd frontend && npm run build
- **Criteria**:
  - Vite bundler must complete with exit code 0.
  - Zero JSX compilation or component import errors.
  - Production assets (dist/index.html, dist/assets/*.css, dist/assets/*.js) generated cleanly.

---

## 4. Multi-Service Container Verification
- **Command**: docker compose config
- **Criteria**:
  - Compose schema must validate all 4 service blocks: db, backend, frontend, mediamtx.
  - Environment variables RELAY_INTERNAL_URL and RELAY_PUBLIC_URL properly passed to backend.

---

## 5. Execution Guide
To run the automated verification suite:

`powershell
cd "d:\Heer\Hackathon\I-Hub Gujarat Hackathonackend"
.env\Scripts\python.exe ..	est_e2e_pipeline.py
`
