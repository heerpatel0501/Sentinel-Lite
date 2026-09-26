# Product Requirements Document (PRD)

## 1. Executive Overview & Problem Statement
Modern urban safety and traffic enforcement across Gujarat State depend on tens of thousands of CCTV cameras deployed across major metropolitan hubs (Ahmedabad, Surat, Vadodara, Rajkot, Gandhinagar). However, these cameras are operated in administrative silos by separate government bodies:
- **Gujarat State Police**: Crime prevention, suspect tracking, law enforcement.
- **Regional Transport Office (RTO)**: Vehicle registration verification, commercial compliance, toll/weight enforcement.
- **Gujarat State Road Transport Corporation (GSRTC)**: Public bus depot security, transit corridor monitoring.
- **Municipal Corporations (AMC, SMC, VMC, RMC)**: Smart city operations, traffic intersection management.

These cameras use incompatible, proprietary Video Management Systems (**Milestone XProtect, Genetec Security Center, Hikvision iVMS, Dahua DSS, ONVIF devices**), preventing inter-agency video sharing and cross-department vehicle tracking.

**Sentinel-Lite** provides a unified, vendor-agnostic surveillance command platform combining:
1. **Centralized Geospatial Camera Hardware Registry** (Model 1)
2. **Real Computer Vision AI Vehicle Analytics & Plate OCR Pipeline** (Model 2)
3. **Vendor-Agnostic VMS Federation Middleware** (Model 3)

---

## 2. Target User Personas
| Persona | Role | Key Objectives | Critical Workflows |
|---------|------|----------------|-------------------|
| **Inspector Rajesh Patel** | Gujarat Police Investigator | Track stolen/suspect vehicles across jurisdictional boundaries | Natural language search (Find GJ01-AB-1234), view chronological journey trail, review forensic snapshots. |
| **Pooja Shah** | RTO Enforcement Officer | Verify vehicle registration parameters and identify flagged commercial vehicles | Check watchlist match status, verify issuing RTO office, inspect engine/chassis hash integrity. |
| **Amit Desai** | Municipal Smart City Operator | Monitor city-wide camera telemetry and stream health | Track online/offline status, camera resolutions, FPS, and video latency across geographic wards. |
| **State Surveillance Admin** | IT / Security Administrator | Maintain regulatory compliance, data access audit logs, and hardware registration | Manage role-based access control (RBAC), review DPDP Act statutory audit logs, integrate new camera feeds. |

---

## 3. Core System Models & Functional Requirements

### Model 1: Centralized CCTV Hardware Registry
- **FR-1.1**: Maintain a state-wide database of surveillance hardware cataloging camera ID, name, GPS latitude/longitude, department owner, VMS vendor, resolution, and operational status.
- **FR-1.2**: Provide an interactive GIS vector map (MapLibre GL JS) rendering color-coded pins for each department:
  - 🔵 Police (Blue)
  - 🟠 RTO (Orange)
  - 🟢 GSRTC (Green)
  - 🟣 Municipal (Purple)
- **FR-1.3**: Display real-time telemetry summary metrics: total camera count, system-wide uptime percentage, and connected departments.

### Model 2: Real Computer Vision & Forensic Investigation
- **FR-2.1 (Vehicle Detection)**: Ingest frames and detect vehicles using Ultralytics YOLOv8 (car, 	ruck, us, motorcycle).
- **FR-2.2 (Plate Localization & OCR)**: Localize license plate regions and perform optical character recognition via EasyOCR.
- **FR-2.3 (Plate Normalization)**: Clean OCR artifacts and standardize alphanumeric text into standard Gujarat vehicle syntax (GJ01-AB-1234).
- **FR-2.4 (Forensic Evidence Snapshots)**: Automatically crop keyframe detections to disk (/evidence/snapshots/), compute a cryptographic **SHA-256** integrity hash, and record file metadata in evidence_records.
- **FR-2.5 (No Raw Video in DB)**: Under no circumstances store video files or blobs in PostgreSQL or SQLite. Store structured metadata and URI references only.
- **FR-2.6 (Investigator Search)**: Provide natural language plate search (GET /api/search?plate=...) reconstructing chronological movement trajectories across inter-agency cameras.
- **FR-2.7 (Synthetic Vehicle Profile)**: Return authorized vehicle registration details (maker, model, fuel type, issuing RTO, masked owner contact) to verified investigators.

### Model 3: Vendor-Agnostic VMS Federation Adapter Layer
- **FR-3.1**: Implement an extensible VMSProvider abstract base class with standardized async stream resolution:
  sync def get_stream(self, camera: Any) -> Dict[str, Any]
- **FR-3.2**: Provide concrete adapters for Milestone, Hikvision, Genetec, Dahua, LiveGrid, ONVIF, and Sentinel Official RTSP.
- **FR-3.3**: Support ONVIF protocol translation: discover device profiles, fetch RTSP URIs via onvif-zeep, and relay to MediaMTX for browser playback.
- **FR-3.4 (Official Ingestion)**: Implement dynamic camera discovery via GET /api/ingest (no hardcoded stream URLs).
- **FR-3.5 (Transport & Sync)**: Enforce RTSP over TCP (	ransport=tcp), support mixed H.264/H.265 decompression, and synchronize frames via container Presentation Time Stamps (PTS).

---

## 4. Security, RBAC & Privacy Governance
- **SR-1 (Role-Based Access Control)**: Enforce 3 tiers of authorization:
  - Admin: Full read/write, audit log inspection, hardware management.
  - Analyst: Threat intelligence, plate search, journey reconstruction, vehicle profiles.
  - Viewer: Read-only registry telemetry. Prohibited from viewing sensitive vehicle profiles (**HTTP 403 Forbidden**).
- **SR-2 (Credential Protection)**: Omit camera credentials and onvif_password from public API responses.
- **SR-3 (Statutory Audit Logging)**: Automatically log every search query and sensitive vehicle profile access into udit_logs supporting DPDP Act 2023 compliance.

---

## 5. Non-Functional Requirements (NFRs)
- **NFR-1 (Performance)**: API query latency for investigator plate search < 100ms for datasets up to 100,000 movements.
- **NFR-2 (Resilience)**: Automatic database fallback from PostgreSQL+PostGIS to local SQLite if PostgreSQL is unavailable.
- **NFR-3 (Reconnection)**: Stream workers implement exponential backoff auto-reconnect (1s, 2s, 4s, 8s, up to 30s) upon stream dropouts.
- **NFR-4 (Extensibility)**: Integrating a new VMS vendor requires only writing a single subclass of VMSProvider.
