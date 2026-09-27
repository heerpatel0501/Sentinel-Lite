# Sentinel Lite API Contract

## 1. API base

All application endpoints are versioned under:

```text
/api/v1
```

## 2. Authentication

```text
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

## 3. VMS

```text
GET    /api/v1/vms
POST   /api/v1/vms
GET    /api/v1/vms/{id}
PATCH  /api/v1/vms/{id}
DELETE /api/v1/vms/{id}
POST   /api/v1/vms/{id}/sync
GET    /api/v1/vms/{id}/health
```

## 4. Cameras

```text
GET    /api/v1/cameras
POST   /api/v1/cameras
GET    /api/v1/cameras/{id}
PATCH  /api/v1/cameras/{id}
DELETE /api/v1/cameras/{id}
GET    /api/v1/cameras/{id}/health
GET    /api/v1/cameras/{id}/events
GET    /api/v1/cameras/{id}/stream
```

## 5. Events

```text
GET  /api/v1/events
GET  /api/v1/events/{id}
POST /api/v1/events
```

Supported filters should include camera, department, event type, time range, confidence and status.

## 6. Candidate events

```text
GET  /api/v1/candidates
GET  /api/v1/candidates/{id}
POST /api/v1/candidates/{id}/verify
POST /api/v1/candidates/{id}/reject
```

## 7. Investigations

```text
GET    /api/v1/investigations
POST   /api/v1/investigations
GET    /api/v1/investigations/{id}
PATCH  /api/v1/investigations/{id}
GET    /api/v1/investigations/{id}/timeline
GET    /api/v1/investigations/{id}/evidence
POST   /api/v1/investigations/{id}/evidence
```

## 8. Dashboard

```text
GET /api/v1/dashboard/summary
```

## 9. Users/departments/audit

```text
GET/POST/PATCH /api/v1/users
GET             /api/v1/departments
GET             /api/v1/audit
```

Exact authorization for each operation is defined in `SECURITY.md`.

## 10. Canonical camera object

```json
{
  "camera_id": "CAM-001",
  "name": "Main Road Camera",
  "department": "Traffic",
  "location": {
    "lat": 23.0225,
    "lng": 72.5714
  },
  "vendor": "VendorA",
  "vms_type": "ONVIF",
  "status": "online"
}
```

## 11. Canonical event object

```json
{
  "event_id": "EVT-001",
  "camera_id": "CAM-001",
  "event_type": "vehicle_detected",
  "timestamp": "2026-09-26T13:00:00Z",
  "confidence": 0.91,
  "metadata": {},
  "status": "new"
}
```

## 12. Error envelope

```json
{
  "error": {
    "code": "CAMERA_NOT_FOUND",
    "message": "Camera CAM-001 does not exist",
    "request_id": "req-123"
  }
}
```

## 13. Realtime events

The backend may emit events such as:

```text
camera.status_changed
event.created
event.updated
candidate.created
candidate.verified
investigation.updated
vms.health_changed
```

Payloads should contain event name, timestamp, resource identifier and the minimum state needed by the consumer.
