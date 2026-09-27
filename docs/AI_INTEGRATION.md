# AI Integration Contract

## 1. Purpose

AI is an external capability from the backend's perspective. The backend stores and orchestrates AI results but should not be tightly coupled to one model runtime.

## 2. Initial capability scope

The project identifies:

- person detection;
- vehicle detection;
- number-plate detection/OCR where feasible;
- event classification;
- cross-camera assistance;
- confidence scoring.

## 3. Request flow

```text
Event / frame reference
      ↓
AI request
      ↓
AI service
      ↓
Structured detection result
      ↓
Backend
      ↓
Event / candidate enrichment
```

## 4. Result contract

```json
{
  "request_id": "AI-1042",
  "event_id": "EVT-001",
  "detections": [
    {
      "type": "vehicle",
      "confidence": 0.94,
      "attributes": {}
    }
  ]
}
```

## 5. Backend responsibilities

- validate AI result schema;
- associate result with event/camera;
- store provenance/model metadata where needed;
- feed relevant information into correlation;
- preserve raw/structured evidence references.

## 6. Model independence

The backend should not assume YOLO specifically. The project mentions YOLO/computer-vision frameworks as candidates, so model choice remains replaceable.

## 7. Failure behavior

AI outage must not prevent basic VMS event ingestion. AI enrichment can remain pending or unavailable while the underlying event persists.
