# Sentinel-Lite Gujarat CCTV Integration — System Architecture

This document defines and locks the authoritative system and cloud architecture decisions for **Sentinel-Lite**, the Gujarat State Surveillance and Multi-Agency CCTV Federation Gateway.

---

## 1. Redis as the Real-Time Event & Messaging Layer
**Redis** is locked as the real-time event bus and publish/subscribe messaging layer.

### Responsibilities
- Real-time vehicle detection events (`event_type: "vehicle_detection"`)
- License plate recognition events (`event_type: "plate_recognition"`)
- Real-time inter-agency security alerts (`event_type: "alert"`)
- Camera and stream telemetry status updates (`event_type: "camera_status"`)
- Live dashboard fanout via WebSockets (`/ws` and `/api/v1/ws`)

### Queue & Pub/Sub Topology
- **Redis Pub/Sub Channel**: `sentinel:events` (immediate, non-blocking fanout to connected operator dashboards).
- **Redis List Queue**: `sentinel:queue` (LPUSH / RPOP queue for background worker processing).
- **Dead-Letter Queue**: `sentinel:queue:dlq` (for handling persistently failed messages).
- **Migration note**: Sentinel-Lite previously referenced RabbitMQ. RabbitMQ has been removed and replaced entirely by Redis. Sentinel-Lite does not maintain both brokers.
- **Resilience**: The system fails clearly if Redis is required (e.g., in production via `REQUIRE_REDIS=true` or `ENVIRONMENT=production`) but unreachable, avoiding silent event loss. In local headless development environments without Redis, a thread-safe `InMemoryQueue` fallback is provided.

---

## 2. PostgreSQL as the Persistent Source of Truth
**PostgreSQL (with PostGIS)** is the permanent relational database and authoritative source of truth.

### Responsibilities
- All relational entity records: cameras, departments, users, roles, and VMS provider registrations.
- Persistent audit logs: immutable access logs with HMAC SHA-256 signatures for non-repudiation.
- Permanent investigation data:
  - `vehicle_detections`: timestamp, vehicle type, normalized bounding box, confidence, evidence URI.
  - `plates`: detected plate text, normalized Gujarat plate (`GJ\d{2}[A-Z]{1,2}\d{4}`), OCR confidence.
  - `vehicle_movements`: historical trail across cameras and departments for cross-jurisdictional correlation.
  - `alerts`: watchlist hits and cross-department correlation alerts.
  - `evidence_records`: cryptographic SHA-256 hashes, file URIs, PTS timestamps, file size.
- **Zero raw video in PostgreSQL**: Video streams and raw video files are **never** stored inside PostgreSQL. Only snapshot image references and SHA-256 checksums are stored.
- Redis must **never** replace PostgreSQL as the permanent investigation database.

---

## 3. ALB as the Current AWS External API Entry Point
For the current AWS architecture, an **AWS Application Load Balancer (ALB)** is locked as the external HTTP/HTTPS entry point.

### Traffic Flow
```text
Internet
   │
   ▼
AWS Application Load Balancer (ALB)
   ├── Port 80 / 443 ──► Forward to ALBTargetGroup (FastAPI container :8000)
   └── Port 8888 ──────► Forward to ALBWebRTCTargetGroup (MediaMTX container :8888)
   │
   ▼
Amazon ECS / AWS Fargate Tasks
   ├── Container: sentinel-api (:8000)
   └── Container: sentinel-mediamtx-sidecar (:8554, :8888)
```

- ALB provides direct SSL/TLS termination, health checking (`/health`), path-based routing, and connection balancing across ECS Fargate tasks.

---

## 4. API Gateway is Not Part of the Current Architecture
**AWS API Gateway is explicitly NOT used** in Sentinel-Lite.

### Rationale
- The current deployment targets ECS/Fargate container workloads. An ALB natively terminates HTTP/HTTPS, handles persistent WebSocket connections (`/ws`), and streams WebRTC traffic (:8888) without API Gateway payload size limits (10 MB limit in API Gateway vs high-throughput binary frames/evidence) or execution timeout limitations (29-second API Gateway timeout).
- Maintaining both API Gateway and ALB introduces unnecessary network hops, billing overhead, and operational latency.
- Any legacy documentation references to "API Gateway" are deprecated in favor of the ALB.

---

## 5. Locked CCTV → AI Processing Pipeline

The end-to-end video ingestion and analytical pipeline is locked as follows:

```text
Official CCTV / RTSP Stream
   │
   ▼
MediaMTX (RTSP/WebRTC/HLS Relay)
   │
   ▼
SentinelStreamWorker (TCP Transport + PTS Tracking)
   │
   ▼
SentinelAIEngine (YOLOv8 Vehicle Detection)
   │
   ▼
License Plate Detector (CRAFT / Bounding Box Crop)
   │
   ▼
EasyOCR (Character Recognition Engine)
   │
   ▼
Gujarat Plate Normalizer (GJ\d{2}[A-Z]{1,2}\d{4})
   │
   ├───────────────────────────────┐
   ▼                               ▼
PostgreSQL (RDS)                 Redis (ElastiCache)
[Persistent Storage]             [Real-Time Fanout]
- vehicle_detections             - Pub/Sub (sentinel:events)
- plates & normalizations        - Queue (sentinel:queue)
- vehicle_movements              - camera_status telemetry
- alerts (watchlist/cross-dept)  │
- evidence_records (SHA-256)     │
   │                             │
   ▼                             ▼
Investigator Search & Evidentiary  Live Command Center
Trail / PDF Reports              Dashboard & WebSockets
```

---

## 6. Distinction: Redis vs PostgreSQL

| Dimension | Redis | PostgreSQL |
| :--- | :--- | :--- |
| **Primary Role** | Real-time messaging & transient event bus | Persistent source of truth & relational ledger |
| **Data Lifecycle** | Ephemeral / short-lived | Permanent / audited / durable |
| **Use Cases** | Live WebSocket fanout, queue buffering, real-time alerts, stream heartbeats | Historical search, cross-camera vehicle tracking, watchlist lookup, evidence chain-of-custody |
| **Storage Model** | In-memory with optional append-only file persistence | Durable ACID relational storage (PostGIS) |
| **Evidentiary Status**| Not for permanent legal evidence | Authoritative legal record with SHA-256 signatures |

---

## 7. Distinction: MediaMTX vs AI Worker

| Component | MediaMTX | SentinelStreamWorker / AI Worker |
| :--- | :--- | :--- |
| **Core Function** | Video ingestion, multiplexing, protocol conversion (RTSP $\to$ WebRTC/HLS) | Computer vision inference, OCR, and analytical correlation |
| **Data Handled** | Raw H.264/H.265 video packets | Decoded image frames (numpy arrays) |
| **Output** | Low-latency WebRTC/HLS stream URLs for operator browsers | Bounding boxes, vehicle classes, plate numbers, alerts, cryptographic hashes |
| **Execution Plane**| High-performance C/Go media relay sidecar | Python multiprocessing/threading AI inference engine |

---

## 8. Local Development vs Official Sentinel RTSP Integration

### Official Sentinel RTSP Architecture
- **Discovery**: Dynamic runtime discovery via `GET /api/ingest`. Queries the official camera catalogue for RTSP endpoints, geographic coordinates, and departmental ownership.
- **Protocol**: RTSP over TCP (`rtsp_transport;tcp`) to prevent packet loss across municipal networks.
- **Timing**: Container PTS timestamps are captured and preserved throughout inference and evidence metadata.
- **Resilience**: Exponential reconnect backoff (1s, 2s, 4s... max 30s) with frame gap tolerance.
- **Security**: Sentinel never publishes/pushes streams back to the official government system. Ingestion is strictly read-only.

### Local Development / Simulation
- When the official RTSP endpoints are unreachable or running without network access to the camera grid, `USE_LOCAL_FALLBACK=true` utilizes `traffic_sample.mp4` to simulate CCTV feeds.
- The pipeline processes simulated frames through the identical YOLOv8 + OCR + Normalization + PostgreSQL + Redis flow, ensuring 100% parity between local testing and production.

---

## 9. AWS Deployment Architecture

```text
                                Internet
                                   │
                                   ▼
                    [AWS Application Load Balancer]
                     Port 80/443 (HTTP/S) & 8888 (WebRTC)
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
        [Public Subnet 1 (10.0.1.0/24)] [Public Subnet 2 (10.0.2.0/24)]
                     │                           │
                     └─────────────┬─────────────┘
                                   │
                                   ▼
                       [ECS Fargate Cluster]
             ┌───────────────────────────────────────────┐
             │ Sentinel Task Definition (2 vCPU, 4GB)    │
             │  ├── Container: sentinel-api (:8000)      │
             │  │     FastAPI + AI Engine + Event Worker │
             │  └── Container: sentinel-mediamtx-sidecar │
             │        MediaMTX Relay (:8554, :8888)      │
             └───────────────────────────────────────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     │ Private Subnets (10.0.10.0 & 10.0.20.0)
                     ▼                           ▼
        [Amazon RDS PostgreSQL]       [Amazon ElastiCache Redis]
         - Multi-AZ Enabled            - Redis Cluster Mode
         - PostGIS Extension           - Private VPC Ingress Only
         - Encrypted Storage (KMS)     - Subnet Group Isolation
```

### Infrastructure Provisioning
- Managed via `deploy/aws/cloudformation.yaml` and `deploy/aws/ecs-task-definition.json`.
- Secrets management: Database credentials, Redis URLs, and JWT signing keys are injected securely at runtime via AWS Secrets Manager (`arn:aws:secretsmanager:ap-south-1:...`).
