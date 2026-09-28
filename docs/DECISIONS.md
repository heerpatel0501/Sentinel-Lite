# Architecture Decision Records (ADRs)

## ADR-001: SQLite for dev, PostgreSQL+PostGIS for production
**Decision:** Run natively on SQLite during development; target PostgreSQL+PostGIS for production.  
**Reason:** Docker was not available during initial development, and native SQLite meant zero setup friction. PostGIS is needed for real geospatial queries and concurrent multi-department writes, which SQLite cannot handle at production scale. ackend/database.py includes automatic fallback so both work seamlessly.

## ADR-002: FastAPI over Flask/Django
**Decision:** Use FastAPI for the backend.  
**Reason:** Native async support handles multiple simultaneous camera streams without blocking; auto-generated OpenAPI docs reduce documentation overhead; Pydantic validation is built in.

## ADR-003: MapLibre GL JS + OpenStreetMap over Google Maps
**Decision:** Use MapLibre GL JS with OpenStreetMap tiles for the GIS registry map.  
**Reason:** No API key or billing required, fully open-source, and sufficient for pin-based camera visualization. Avoids vendor lock-in for a government platform.

## ADR-004: Vendor adapter pattern for VMS federation
**Decision:** Implement VMS federation as an abstract VMSProvider base class with one subclass per vendor, rather than branching logic per vendor inline.  
**Reason:** This is the actual technical substance of 'Model 3' — new vendors are added by writing one new class, without touching existing code. Makes the system genuinely extensible, not just demo-shaped.

## ADR-005: Decoupled AI Pipeline with EasyOCR & Dedicated Plate Detection
**Decision:** Implement real vehicle detection with Ultralytics YOLOv8, combined with high-confidence license plate localization and EasyOCR character recognition.  
**Reason:** Replaces simple heuristic contours with real neural text recognition and standardizes Indian plates (GJ01-AB-1234), outputting cryptographic SHA-256 evidence crops.

## ADR-006: RabbitMQ event-correlation service kept separate
**Decision:** A teammate's RabbitMQ-based event correlation microservice (motion+door correlation, loitering/tailgating detection) is built and tested standalone but not merged into the core app yet.  
**Reason:** Adding a new infrastructure dependency (RabbitMQ, Docker) late in development risked destabilizing a working core demo. It is tracked as future work (Phase 9 in TASKS.md) with a clear integration path (HTTP bridge into the alerts table) once the core is stable.

## ADR-007: hls.js for live stream playback
**Decision:** Use hls.js on the frontend to play .m3u8 HLS streams.  
**Reason:** Browsers do not natively play HLS outside Safari; hls.js is the standard, lightweight solution and works with both mocked and real government test-grid streams.

## ADR-008: MediaMTX for RTSP-to-HLS and ONVIF Stream Relaying
**Decision:** Integrate MediaMTX as a lightweight, low-latency relay sidecar in docker-compose.yml.  
**Reason:** Web browsers cannot directly play raw RTSP/UDP streams. MediaMTX converts incoming RTSP streams into HLS/WebRTC with minimal CPU overhead, enabling seamless browser viewing while supporting container-internal networking (http://mediamtx:8888) and public browser access (http://localhost:8888).

## ADR-009: PTS-Based Chrono-Sequencing over FPS/Arrival Time
**Decision:** Frame synchronization and inter-camera tracking rely on Presentation Time Stamps (PTS) embedded in RTSP packets, rather than client frame arrival time or CAP_PROP_FPS.  
**Reason:** Network jitter across municipal WANs causes variable frame arrival times. Using packet PTS guarantees millisecond-accurate cross-agency vehicle trajectory tracking regardless of network latency.
