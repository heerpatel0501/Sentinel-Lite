# Cross-Camera Correlation

## 1. Purpose

The correlation engine identifies groups of events that may describe the same movement/activity across multiple cameras.

## 2. Inputs

Potential signals:

- event timestamp;
- camera location;
- camera relationships;
- event type;
- vehicle/person attributes;
- plate/OCR result where available;
- direction or path metadata;
- detection confidence.

## 3. Camera relationship model

A future/advanced registry may store:

```text
camera_a
camera_b
road_segment
expected_travel_seconds_min
expected_travel_seconds_max
direction
```

This allows correlation to reason about plausible movement rather than simple geographic distance.

## 4. Example

```text
CAM-A vehicle_detected @ 14:32:01
CAM-B vehicle_detected @ 14:32:17
CAM-C vehicle_detected @ 14:32:39

              ↓
       Correlation Engine
              ↓
       Candidate Event
```

## 5. Candidate state

```text
CREATED
  ↓
CANDIDATE
  ↓
UNDER_REVIEW
 ├── VERIFIED
 └── REJECTED

VERIFIED → INVESTIGATION → CLOSED
```

## 6. Confidence

Keep distinct concepts distinct:

```text
Detection confidence
Correlation confidence
Candidate confidence
```

Do not collapse all model/relationship evidence into one unexplained percentage.

## 7. Explainability

A candidate should retain enough evidence to answer:

- which events caused it;
- which cameras were involved;
- what time relationship existed;
- what spatial/path relationship existed;
- which AI evidence contributed;
- what confidence components were used.

## 8. MVP correlation

Start with deterministic rules such as:

```text
time window
+
nearby/related cameras
+
matching event/object attributes when available
```

Sophisticated probabilistic ranking can be added later.
