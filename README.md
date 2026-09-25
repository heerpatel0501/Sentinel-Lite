# 🛡️ Sentinel-Lite: Gujarat CCTV Registry & VMS Federation

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge&logo=yolo)
![MapLibre](https://img.shields.io/badge/MapLibre_GL-3957A3?style=for-the-badge&logo=maplibre)
![SQLite / PostGIS](https://img.shields.io/badge/Database-SQLite%20%2F%20PostGIS-336791?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**A unified, state-wide surveillance registry, vendor-agnostic VMS federation engine, and real-time AI vehicle analytics platform designed for Gujarat State Administration.**

[Key Features](#-key-features) • [Architecture](#-system-architecture) • [Lead Contributor](#-lead-contributor--developer) • [Getting Started](#-getting-started) • [API Reference](#-api-reference)

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
