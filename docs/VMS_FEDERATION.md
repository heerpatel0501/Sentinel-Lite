# VMS Federation and Connector Design

## 1. Purpose

The federation layer hides vendor-specific protocols and payloads behind a stable connector interface.

## 2. Connector interface

Conceptual operations:

```text
discover_cameras()
get_camera()
get_camera_status()
get_stream_info()
fetch_events()
subscribe_events()
health_check()
```

Not every connector must implement every operation. Unsupported capabilities should be explicit.

## 3. Connector lifecycle

```text
REGISTERED
  ↓
CONNECTING
  ↓
CONNECTED
  ↓
DEGRADED / OFFLINE
  ↓
RECONNECTING
  ↓
CONNECTED
```

## 4. Supported integration styles

The project calls out:

- ONVIF
- RTSP
- vendor-specific APIs

The first hackathon implementation can use mock connectors to demonstrate federation before real vendor integrations are ready.

## 5. Normalization

Example:

```text
Vendor A: device_id, camera_name, lat, lon
Vendor B: deviceId, cameraName, latitude, longitude
                ↓
        Sentinel Camera Model
```

## 6. Source lineage

Never discard source context. Persist or trace:

```text
source VMS
source device/camera ID
connector identity
last synchronization time
raw metadata reference when required
```

## 7. Failure isolation

A connector failure must be isolated from unrelated VMS sources.

## 8. Mock VMS strategy

For the hackathon, create at least three deterministic/mock sources:

```text
Police VMS
Traffic VMS
RTO VMS
```

Each should expose slightly different source payload shapes so normalization is demonstrated rather than merely claimed.

## 9. Real-vendor boundary

The backend should not depend on a specific vendor's SDK throughout the application. Vendor SDK/protocol logic stays inside the connector package.
