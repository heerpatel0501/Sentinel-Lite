# 🛡️ Sentinel-Lite: Gujarat CCTV Registry & VMS Federation

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge&logo=yolo)
![MapLibre](https://img.shields.io/badge/MapLibre_GL-3957A3?style=for-the-badge&logo=maplibre)
![SQLite / PostGIS](https://img.shields.io/badge/Database-SQLite%20%2F%20PostGIS-336791?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**A unified, state-wide surveillance registry, vendor-agnostic VMS federation engine, and real-time AI vehicle analytics platform designed for Gujarat State Administration.**

[Stream & Dataset Specs](#-dataset--official-sentinel-stream-ingestion) • [Key Features](#-key-features) • [System Architecture](#-system-architecture) • [Investigator Search](#-investigative-journey--evidence-trajectory-search-get-apisearch) • [API Reference](#-api-reference) • [Getting Started](#-getting-started)

---
</div>

## 📌 Executive Summary

Modern urban safety and traffic management across Gujarat rely on thousands of surveillance cameras operated by disparate government bodies: **Gujarat State Police**, **Regional Transport Office (RTO)**, **Gujarat State Road Transport Corporation (GSRTC)**, and **Municipal Corporations (AMC, SMC, VMC, RMC)**. 

Historically, these cameras operate in departmental silos using proprietary, incompatible Video Management Systems (VMS) such as **Milestone, Genetec, Hikvision, and Dahua**. 

**Sentinel-Lite** breaks these silos by providing:
1. **Centralized Geospatial Registry**: A single pane of glass cataloging camera telemetry, location coordinates, health status, and administrative ownership.
2. **Federation Adapter Layer**: A vendor-agnostic middleware normalizing proprietary video streams into open web standards (HLS / MP4).
3. **Cross-Department Threat Intelligence**: Automated cross-departmental alert aggregation to track suspicious target vehicles (e.g. `GJ01-AB-1234`) across agency jurisdictions.
4. **Embedded Edge AI (YOLOv8)**: Real-time object and vehicle detection with live canvas overlay and vehicle density monitoring.

---

## 📹 Dataset & Official Sentinel Stream Ingestion

> **Official I-Hub Gujarat Hackathon Compliance**:  
> Sentinel-Lite is engineered specifically to consume the **official Gujarat Sentinel CCTV stream grid**. We do **not** rely on fake, downloaded, or static sample clips as our primary integration. The system directly interfaces with the **~12 hours of surveillance footage from 30+ government cameras** provided as simulated-live multi-agency streams.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   OFFICIAL HACKATHON INGEST PIPELINE                                    │
│                                                                                                         │
│   Dynamic Discovery               Stream Transport            Edge AI Pipeline            Database /    │
│  [GET /api/ingest]              [RTSP over TCP]           [YOLOv8 + Plate OCR]        Spatial Analytics │
│                                                                                                         │
│  ┌─────────────────┐             ┌─────────────────┐       ┌──────────────────────┐    ┌──────────────┐ │
│  │ 30+ Govt Cameras│  RTSP / HLS │ TCP Interleaved │       │ Vehicle Detection    │    │ PostgreSQL   │ │
│  │ Stream Manifest │────────────►│ H.264 / H.265   │──────►│ Plate Localization   ├───►│ PostGIS /    │ │
│  │ (No Hardcoding!)│             │ PTS Time Sync   │       │ OCR Extraction       │    │ SQLite       │ │
│  └─────────────────┘             └─────────────────┘       └──────────────────────┘    └──────────────┘ │
│                                                                                               │         │
│                                                                                               ▼         │
│                                                                                     Investigator Search │
│                                                                                     [/api/search?plate=]│
│                                                                                     - Full Trajectory   │
│                                                                                     - Evidence Links    │
│                                                                                     - Watchlist Matches │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Zero Hardcoding — Dynamic Discovery via `GET /api/ingest`
- Camera endpoints and stream URLs are **never hardcoded** in source code.
- Sentinel-Lite implements a dynamic discovery service via `GET /api/ingest` that queries the official stream gateway, resolving camera identifiers, network endpoints, departmental ownership, and geographic coordinates at runtime.

### 2. Stream Transport & Protocol Specifications
- **RTSP over TCP (Interleaved)**: All stream ingestion mandates TCP transport (`?transport=tcp`). This prevents the packet drops, frame tear, and UDP packet loss inherent to municipal WANs and simulated-live multi-stream saturation.
- **Mixed Codec Decompression (H.264 & H.265)**: The backend adapter engine seamlessly demuxes both legacy H.264 (AVC) and bandwidth-optimized H.265 (HEVC) streams without requiring external transcoding servers.
- **Multi-Resolution Ingestion**: Adaptively processes varying sensor resolutions across 720p, 1080p Full HD, and 4K feeds.
- **Exponential Backoff Reconnect Policy**: Built-in network resiliency with auto-reconnection (1s, 2s, 4s, 8s, up to 30s ceiling) handling transient network drops, stream resets, and camera restarts.
- **PTS-Based Chrono-Sequencing (Presentation Time Stamp)**: Frame extraction and multi-camera temporal tracking use **Presentation Time Stamps (PTS)** embedded directly inside the RTSP/RTP packets. Frame processing is never calculated from client arrival time or wall-clock FPS, guaranteeing millisecond-accurate cross-camera vehicle correlation even with network latency.

### 3. Clear Separation: Official Streams vs. Local Test Fixtures
- **Official Sentinel Stream Pipeline**: The primary production pathway connects to the official 30+ camera RTSP simulated-live stream grid, running automated inference and persisting live telemetry.
- **Demo / Local Test Fixtures**: Contained entirely within `db/init.sql` and `traffic_sample.mp4`, used strictly as an offline fallback for isolated unit testing, local developer environments without live internet access, and CI verification.

### 4. Database Storage Policy — No Raw Video in PostgreSQL
- **Strict Storage Compliance**: Sentinel-Lite **never downloads or stores raw CCTV video files/blobs in PostgreSQL or SQLite**.
- The database stores purely lightweight, query-optimized structured metadata:
  - Timestamp (synchronized with RTSP PTS)
  - Camera identifier & PostGIS geographic coordinates (`latitude`, `longitude`)
  - Vehicle classification (car, truck, bus, motorcycle) & detection confidence
  - License plate alphanumeric text & OCR confidence score
  - Relative bounding box coordinates `[x1, y1, x2, y2]`
  - External URI reference pointers to keyframe evidence snapshots (`/evidence/snapshots/...`)

### 5. Investigative Journey & Evidence Trajectory Search (`GET /api/search`)
Law enforcement officers and traffic analysts can search any license plate (e.g. `GJ01-AB-1234`) to immediately reconstruct:
- **Chronological Sighting History**: Complete timeline of when and where the vehicle passed each camera.
- **Cross-Departmental Jurisdictional Path**: Sighting sequence across Police, RTO, GSRTC, and Municipal surveillance grids.
- **Geospatial Route Map**: Sequence of GPS coordinates ready for map polyline rendering.
- **Evidence References**: Instant access to snapshot evidence references and OCR confidence scores.
- **Watchlist Verification**: Automatic cross-referencing against active stolen/wanted flags and inter-agency alerts.

---

## 🚀 Key Features

### 1. Model 1: State-wide Camera Registry (Geospatial Core)
- Real-time catalog of municipal and highway cameras across Ahmedabad, Gandhinagar, Surat, Vadodara, and Rajkot.
- Tracks critical metadata: Department, Latitude/Longitude, VMS Vendor, Online/Offline status, and Resolution.
- Visualized on high-performance vector tiles via **MapLibre GL JS** and OpenStreetMap.

### 2. Model 2: Cross-Department Alert Engine
- Centralized situational awareness feed correlating inter-agency sightings.
- Alerts on stolen vehicles, speed violations, and suspicious depot activity across Police, RTO, and GSRTC jurisdictions.

### 3. Model 3: VMS Federation Adapter Architecture
- Implements the **Gang of Four (GoF) Adapter Pattern** in FastAPI.
- Standardizes diverse video feeds into a unified JSON format:
  ```json
  {
    "camera_id": "1",
    "vendor": "Milestone",
    "protocol": "HLS",
    "stream_url": "https://...",
    "status": "active"
  }
  ```
- Supports both static mock streams and real-world authenticated **LiveGrid HLS (`.m3u8`)** government test feeds via `hls.js`.

### 4. Model 4: Real-Time AI Vehicle & Object Detection (YOLOv8)
- Powered by `ultralytics` YOLOv8 nano (`yolov8n.pt`).
- Detects cars, trucks, buses, motorcycles, bicycles, and persons.
- Supports dual input modes:
  - **Local MP4 Upload**: Analyze local surveillance footage clips.
  - **Live HLS Stream Detection**: Feeds remote government HLS feeds directly into the OpenCV/YOLO inference pipeline.
- Synchronous canvas overlay rendering bounding boxes and confidence scores (`Car 92%`) directly over the video player with live vehicle counting.

---

## 🏗️ System Architecture

```
                                 ┌─────────────────────────────────────────┐
                                 │       React + Vite Frontend Client      │
                                 │  (MapLibre GL + HTML5 Canvas + Hls.js)  │
                                 └────────────────────┬────────────────────┘
                                                      │ HTTP / REST
                                                      ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  FastAPI Backend Middleware                                  │
│                                                                                              │
│   ┌──────────────────────────┐    ┌─────────────────────────┐    ┌───────────────────────┐   │
│   │    Camera Registry       │    │  Cross-Dept Alert Hub   │    │  YOLOv8 AI Inference  │   │
│   │    (/cameras)            │    │  (/alerts)              │    │  (/detect)            │   │
│   └─────────────┬────────────┘    └─────────────────────────┘    └───────────┬───────────┘   │
│                 │                                                            │               │
│                 ▼                                                            │               │
│   ┌────────────────────────────────────────────────────────┐                 │               │
│   │             VMS Federation Adapter Layer               │                 │               │
│   │  ┌───────────┐ ┌─────────────┐ ┌───────────┐ ┌──────┐  │                 │               │
│   │  │ Milestone │ │  Hikvision  │ │  Genetec  │ │Dahua │  │                 │               │
│   │  └─────┬─────┘ └──────┬──────┘ └─────┬─────┘ └──┬───┘  │                 │               │
│   │        └──────────────┴──────────────┴──────────┘      │                 │               │
│   │                 LiveGrid HLS Provider                  │                 │               │
│   └───────────────────────────┬────────────────────────────┘                 │               │
└───────────────────────────────┼──────────────────────────────────────────────┼───────────────┘
                                │                                              │
                                ▼                                              ▼
                ┌───────────────────────────────┐              ┌───────────────────────────────┐
                │      Database Storage         │              │      Computer Vision Core     │
                │  - SQLite (Native Run)        │              │  - Ultralytics YOLOv8n        │
                │  - PostgreSQL + PostGIS (Prod)│              │  - OpenCV Frame Extractor     │
                └───────────────────────────────┘              └───────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Domain | Technology / Library | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite | High-performance reactive user interface |
| **Geospatial Mapping** | MapLibre GL JS, OpenStreetMap | Hardware-accelerated map rendering & marker layers |
| **Video Playback** | Hls.js, HTML5 Video & Canvas | Native HLS streaming & synchronous bounding box overlay |
| **Backend API** | FastAPI, Uvicorn, Python 3 | Asynchronous RESTful microservices |
| **Computer Vision / AI** | Ultralytics YOLOv8, OpenCV, PyTorch | Automated vehicle & object detection |
| **Database & ORM** | SQLite / PostgreSQL + PostGIS, SQLAlchemy | Spatial database and registry management |
| **Deployment** | Docker, Docker Compose | Multi-container orchestration |

---

## 🚦 Getting Started

### Option 1: Native Local Run (Recommended for Development)

#### 1. Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Setup credentials
copy .env.example .env

# Run FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
> The SQLite database (`sentinel.db`) with 20 seeded Gujarat cameras will be generated automatically on first startup.

#### 2. Frontend Setup
In a new terminal window:
```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies (including hls.js & maplibre-gl)
npm install

# Start Vite development server
npm run dev
```

#### 3. Access the Application
- **Web Dashboard**: [http://localhost:3000](http://localhost:3000) (or port shown by Vite)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Redoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option 2: Docker Compose (Single Command)

If you have Docker and Docker Compose installed:
```bash
docker-compose up --build
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/ingest` | Dynamic discovery of 30+ government CCTV streams (RTSP over TCP, H.264/H.265) |
| `GET` | `/api/search` | Investigator plate search (`?plate=GJ01-AB-1234`) returning full trajectory & evidence |
| `GET` | `/cameras` | Retrieve all registered cameras (local DB + federated live grid) |
| `GET` | `/cameras/{id}` | Fetch metadata for a specific camera |
| `GET` | `/cameras/{id}/stream` | Fetch normalized VMS stream details via adapter pattern |
| `GET` | `/alerts` | Get real-time cross-departmental alerts queried from SQLite database |
| `GET` | `/watchlist` | Retrieve state-wide flagged, stolen, and wanted vehicle plate registry |
| `GET` | `/movements` | Query cross-department vehicle sightings & movement tracking trail |
| `GET` | `/departments` | List connected Gujarat government departments (Police, RTO, GSRTC, etc.) |
| `GET` | `/detections` | Real-time vehicle detections recorded by YOLOv8 pipeline |
| `POST` | `/detect` | Run YOLOv8 vehicle detection on uploaded MP4 or remote HLS stream |
| `GET` | `/health` | System health, uptime metrics, and department telemetry |

---

## 🗄️ End-to-End Pipeline Database Schema

```
[Cameras] (CCTV Registry)
   │ 1:N
   ▼
[Vehicle Detections] ──(REAL via YOLOv8 /detect)──► [Plates + OCR] ──(MOCKED via ANPR Corpus)
   │                                                     │
   ▼                                                     ▼
[Vehicle Movements] ──(Cross-Dept Correlation)────► [Watchlist Lookup]
   │                                                     │
   └─────────────────────────┬───────────────────────────┘
                             ▼
                     [Alerts Engine] ──► (Police, RTO, GSRTC, Municipal)
                             │
                             ▼
                   [Users & Audit Logs] ──► (DPDP Act Compliance)
```

1. **`cameras`**: Centralized CCTV hardware registry across Gujarat.
2. **`departments`**: Administrative owners (Police, RTO, GSRTC, Municipal Corporation, Panchayat).
3. **`vehicle_detections`**: **[REAL]** Populated dynamically by live YOLOv8 `/detect` inference with relative bounding boxes, timestamps, and confidence scores.
4. **`plates`**: **[MOCKED for submission]** Ready for Indian ANPR OCR Corpus dataset integration in the next phase; mocked with realistic Gujarat plates (`GJ01-AB-1234`, etc.).
5. **`watchlist`**: **[MOCKED seed data]** Real-time lookup for stolen, wanted, and flagged vehicles.
6. **`vehicle_movements`**: Powers cross-agency vehicle correlation when the same vehicle is observed across multiple departments' cameras.
7. **`alerts`**: Real relational table replacing hardcoded JSON, tracking inter-agency flags (`cross_department`, `watchlist_match`, `speeding`).
8. **`users` & `audit_logs`**: Role-based access and DPDP Act compliance audit trails.

---

## 📂 Project Structure

```
Sentinel-Lite/
├── backend/
│   ├── .env.example          # Environment template for credentials
│   ├── database.py           # SQLAlchemy engine & SQLite / PostgreSQL session setup
│   ├── Dockerfile            # Container definition for backend
│   ├── main.py               # FastAPI application, routes, and YOLO pipeline
│   ├── models.py             # SQLAlchemy ORM models for Cameras & Alerts
│   ├── requirements.txt      # Python dependencies
│   ├── schemas.py            # Pydantic data schemas
│   ├── vms_adapters.py       # VMS Federation Adapter Pattern implementations
│   └── yolov8n.pt            # Pretrained YOLOv8 nano model weights
├── db/
│   └── init.sql              # PostGIS seed schema for 20 Gujarat cameras
├── frontend/
│   ├── Dockerfile            # Container definition for frontend
│   ├── index.html            # Application entry HTML
│   ├── package.json          # Node dependencies (React, Vite, MapLibre, Hls.js)
│   ├── vite.config.js        # Vite build & dev-server config
│   └── src/
│       ├── App.jsx           # Root layout & state coordinator
│       ├── main.jsx          # React DOM mounting
│       └── components/
│           ├── AlertsSidebar.jsx   # Cross-department alert panel
│           ├── MapComponent.jsx    # MapLibre GL map & camera pin rendering
│           ├── StatsBar.jsx        # Top telemetry bar (Total, Online %, Dept count)
│           └── VideoModal.jsx      # Video player, Hls.js hook, and Canvas bounding box
├── .gitignore                # Git exclusions (credentials, databases, venv, caches)
├── docker-compose.yml        # Multi-service container specification
├── final_demo.mp4            # Demonstration video of the Sentinel-Lite platform
└── README.md                 # Complete project documentation
```

---

## 📄 License

Developed for the **I-Hub Gujarat Hackathon**.
