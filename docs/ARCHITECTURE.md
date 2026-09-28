# System Architecture Specification

## 1. Architectural Overview & Design Principles

Sentinel-Lite is architected as a **modular, vendor-agnostic federation gateway** designed for state-level surveillance grids. It decouples high-throughput video ingestion and heavy AI inference from interactive investigator API queries.

`
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         SYSTEM ARCHITECTURE OVERVIEW                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                         │
│  [Official CCTV Grid / 30+ Cameras]    [Proprietary VMS Feeds]           [ONVIF Hardware]               │
│        (12hr Simulated-Live)           (Milestone/Genetec/Hikvision)    (IP Cameras: Port 80/554)       │
│                 │                                  │                                │                   │
│                 ▼                                  ▼                                ▼                   │
│   ┌───────────────────────────┐      ┌───────────────────────────┐    ┌───────────────────────────┐     │
│   │ Dynamic Discovery Gateway │      │   VMS Federation Layer    │    │       ONVIF Adapter       │     │
│   │    (GET /api/ingest)      │      │   (VMSProvider Factory)   │    │  (onvif-zeep Device Mgmt) │     │
│   └─────────────┬─────────────┘      └─────────────┬─────────────┘    └─────────────┬─────────────┘     │
│                 │                                  │                                │                   │
│                 ▼                                  ▼                                ▼                   │
│   ┌───────────────────────────────────────────────────────────────────────────────────────────────┐     │
│   │                  Stream Ingestion Worker Engine & MediaMTX Relay Sidecar                     │     │
│   │  - RTSP over TCP (Interleaved)       - Mixed H.264/H.265 Demuxing     - MediaMTX HLS Bridge  │     │
│   │  - PTS Chrono-Sequencing             - Exponential Backoff Auto-Retry - Stream Health Monitor │     │
│   └───────────────────────────────────────────────┬───────────────────────────────────────────────┘     │
│                                                   │ Decoded Frames + PTS                                │
│                                                   ▼                                                     │
│   ┌───────────────────────────────────────────────────────────────────────────────────────────────┐     │
│   │                           Computer Vision & Forensic AI Pipeline                              │     │
│   │  ┌───────────────────────┐       ┌───────────────────────┐       ┌────────────────────────┐   │     │
│   │  │ Vehicle Detection     │──────►│ Plate Localization    │──────►│ Text Recognition       │   │     │
│   │  │ (Ultralytics YOLOv8)  │       │ (Neural Text ROI)     │       │ (EasyOCR Engine)       │   │     │
│   │  └───────────────────────┘       └───────────────────────┘       └───────────┬────────────┘   │     │
│   │                                                                              │                │     │
│   │                 Saves Cryptographic Evidence Snapshot                        ▼                │     │
│   │                 to /evidence/snapshots/<file>.jpg           Normalized Plate: GJ01-AB-1234    │     │
│   │                 Calculates Forensic SHA-256 Hash            Generates URI Pointer Reference   │     │
│   └───────────────────────────────────────────────┬───────────────────────────────────────────────┘     │
│                                                   │ Structured Metadata Only (Zero Raw Video)           │
│                                                   ▼                                                     │
│   ┌───────────────────────────────────────────────────────────────────────────────────────────────┐     │
│   │                 Resilient Multi-Engine Database Layer (PostgreSQL / SQLite)                   │     │
│   │   Primary: PostgreSQL 15 + PostGIS Spatial Engine                                            │     │
│   │   Fallback: SQLite Engine with Runtime Column Inspector Migration                             │     │
│   │   Tables: cameras, departments, vehicle_detections, plates, vehicle_movements, watchlist,    │     │
│   │           alerts, users, audit_logs, stream_health, evidence_records                          │     │
│   └───────────────────────────────────────────────┬───────────────────────────────────────────────┘     │
│                                                   │ RESTful Endpoints (FastAPI)                         │
│                                                   ▼                                                     │
│   ┌───────────────────────────────────────────────────────────────────────────────────────────────┐     │
│   │                       Investigator Command & Control Frontend Dashboard                       │     │
│   │  - MapLibre GL Vector Map               - Live Alerts Sidebar Feed                            │     │
│   │  - Natural Language Search Bar          - Full Investigator Dossier Modal                     │     │
│   │  - Chronological Trajectory Trail       - Cryptographic Evidence Zoom Viewer                  │     │
│   └───────────────────────────────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
`

---

## 2. Core Architectural Subsystems

### Subsystem A: Stream Discovery & Ingestion Gateway
- **Zero Hardcoding**: Camera hardware endpoints are resolved dynamically via GET /api/ingest.
- **RTSP over TCP Transport**: Enforces interleaved TCP framing (
tsp_transport;tcp) within the OpenCV FFmpeg backend to prevent UDP packet drops across municipal WAN networks.
- **Mixed Codec Handling**: Ingests both H.264 (AVC) and H.265 (HEVC) streams across 720p, 1080p, and 4K resolutions.
- **PTS Chrono-Sequencing**: Frame extraction derives timestamps from container Presentation Time Stamps (PTS), ensuring frame synchronization matches camera shutter capture rather than network arrival time.
- **Auto-Reconnect**: Exponential backoff reconnect policy (1s, 2s, 4s, 8s, up to 30s ceiling) protects against network drops and logs channel telemetry in stream_health.

### Subsystem B: VMS Federation & MediaMTX Relay
- **Adapter Pattern (VMSProvider)**: Standardized asynchronous contract:
  `python
  class VMSProvider(ABC):
      @abstractmethod
      async def get_stream(self, camera: Any) -> Dict[str, Any]: ...
      async def check_status(self, camera: Any) -> str: ...
  `
- **MediaMTX Sidecar Networking**:
  - RELAY_INTERNAL_URL = http://mediamtx:8888 (for container-to-container service calls).
  - RELAY_PUBLIC_URL = http://localhost:8888 (for host browser playback via hls.js).
- **ONVIF Device Translation**: Utilizes onvif-zeep to authenticate with IP cameras, retrieve media profile tokens, extract RTSP URIs, and map them to MediaMTX HLS endpoints.

### Subsystem C: Edge Computer Vision Pipeline
- **Vehicle Classification**: YOLOv8 neural network (yolov8n.pt) detects vehicles and extracts bounding coordinates.
- **Dedicated Plate Detector**: Refines vehicle crops using high-confidence neural text ROI detection rather than heuristic edge contours.
- **EasyOCR Recognition**: Extracts alphanumeric characters and cleans noise.
- **Plate Normalizer**: Converts text variations into standard Indian registration format (GJ01-AB-1234).
- **Forensic Snapshot Generator**:
  - Crops vehicle bounding box with visual telemetry overlay (Camera ID, PTS, timestamp).
  - Calculates a cryptographic **SHA-256** hash of the image file.
  - Persists image to /evidence/snapshots/ and stores URI pointer in database.

### Subsystem D: Resilient Database Persistence Tier
- **Dual-Engine Architecture**: Connects to PostgreSQL with PostGIS primarily. If PostgreSQL is unavailable (e.g. running locally without Docker), it automatically activates SQLite with thread safety enabled.
- **Runtime Schema Migration**: On startup, ensure_schema_compatibility(engine) inspects existing SQLite tables using SQLAlchemy inspector. It adds missing columns (cameras.onvif_host, plates.normalized_plate, ehicle_movements.detection_id) via standard ALTER TABLE, avoiding invalid SQLite IF NOT EXISTS syntax.
- **Full Traceability**: ehicle_movements.detection_id references ehicle_detections.id, establishing an unbroken chain of custody from sighting to image crop.

---

## 3. Data Flow & Sequence Diagram

`
[CCTV Camera]      [stream_worker]      [SentinelAIEngine]       [Database]       [Investigator UI]
      │                   │                     │                    │                   │
      │ 1. RTSP Stream    │                     │                    │                   │
      ├──────────────────►│                     │                    │                   │
      │                   │ 2. Extract Frame+PTS│                    │                   │
      │                   ├────────────────────►│                    │                   │
      │                   │                     │ 3. YOLO Detect     │                   │
      │                   │                     │ 4. OCR Extract     │                   │
      │                   │                     │ 5. Save Snapshot   │                   │
      │                   │                     │ 6. Hash SHA-256    │                   │
      │                   │                     ├───────────────────►│                   │
      │                   │                     │  Insert Detection, │                   │
      │                   │                     │  Plate, Movement   │                   │
      │                   │                     │                    │ 7. Natural Search │
      │                   │                     │                    │    GET /api/search│
      │                   │                     │                    │◄──────────────────┤
      │                   │                     │                    │ 8. Trajectory +   │
      │                   │                     │                    │    Evidence URIs  │
      │                   │                     │                    ├──────────────────►│
`

---

## 4. Entity-Relationship Model (11 Tables)

| Table | Primary Key | Key Foreign Keys | Purpose |
|-------|-------------|------------------|---------|
| cameras | id | - | Hardware registry, GPS, VMS vendor, ONVIF connection info. |
| departments | id | - | Administrative bodies (Police, RTO, GSRTC, Municipal, Panchayat). |
| stream_health | id | camera_id -> cameras.id | Live stream telemetry (FPS, PTS, codec, reconnect attempts). |
| ehicle_detections | id | camera_id -> cameras.id | AI vehicle detections, confidence, bounding boxes, PTS timestamp. |
| plates | id | detection_id -> vehicle_detections.id | Localized plate text, normalized plate, OCR confidence. |
| ehicle_movements | id | camera_id, department_id, detection_id | Cross-department journey trail with full evidence traceability. |
| evidence_records | id | detection_id -> vehicle_detections.id | Snapshot file paths, URI references, SHA-256 hashes, file sizes. |
| watchlist | id | - | Stolen/wanted/flagged vehicle registry. |
| lerts | id | - | Cross-department alerts, speeding violations, watchlist hits. |
| users | id | department_id -> departments.id | User identity and RBAC role (dmin, nalyst, iewer). |
| udit_logs | id | user_id -> users.id | Privacy governance and statutory access accountability trail. |
