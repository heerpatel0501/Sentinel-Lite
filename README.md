# Member 3 — Event Processing + Correlation (Sentinel Lite)

Owns: **event normalization, RabbitMQ messaging, and correlation** between
raw events coming from Member 2 (VMS/CCTV) and sensors, producing enriched
"correlated incident" events for Member 4 (dashboard) and Member 6 (AI/analytics).

```
Member 2 (cameras/sensors) --publish raw--> RabbitMQ --consume--> Member 3
                                                                     |
                                                        normalize -> correlate
                                                                     |
                                                          publish processed
                                                                     |
                                              RabbitMQ --consume--> Member 4 / Member 6
```

## 1. Folder structure

```
sentinel-lite-event-processor/
├── README.md
├── requirements.txt
├── docker-compose.yml          # RabbitMQ (with management UI)
├── config/
│   └── config.yaml             # exchange/queue names, correlation window, rules
├── src/
│   ├── __init__.py
│   ├── models.py                # RawEvent / NormalizedEvent / CorrelatedIncident schemas
│   ├── rabbitmq_client.py       # connection + publish/consume helpers (with retry)
│   ├── topology.py              # declares exchanges/queues/bindings + DLQ
│   ├── normalizer.py            # vendor-specific -> canonical event mapping
│   ├── correlation_engine.py    # sliding time-window correlation rules
│   ├── consumer.py              # consumes raw events, runs normalize+correlate
│   ├── producer.py              # publishes normalized/correlated events
│   └── main.py                  # entrypoint wiring everything together
├── sample_events/
│   ├── raw_motion.json
│   ├── raw_face_detect.json
│   ├── raw_door_sensor.json
│   ├── raw_line_crossing.json
│   └── correlated_incident_output.json
├── scripts/
│   └── publish_test_events.py   # simulates Member 2 publishing raw events
└── tests/
    └── test_correlation.py
```

## 2. Step-by-step setup

### Step 1 — Start RabbitMQ
```bash
docker compose up -d
```
This starts RabbitMQ with the management UI at http://localhost:15672
(user: `sentinel`, pass: `sentinel_pw` — change in `docker-compose.yml` for anything
beyond local dev).

### Step 2 — Create a virtualenv and install dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3 — Declare the RabbitMQ topology (exchanges, queues, DLQ)
```bash
python -m src.topology
```
This is idempotent — safe to re-run any time (e.g. after a RabbitMQ restart
with a fresh volume).

### Step 4 — Start the event processor (consumer + normalizer + correlator + producer)
```bash
python -m src.main
```
Leave this running. It will log each raw event it consumes, the normalized
form, and any correlated incidents it raises.

### Step 5 — Simulate Member 2 publishing raw camera/sensor events
In a second terminal:
```bash
python scripts/publish_test_events.py --scenario intrusion
```
Watch the `main.py` terminal — you should see a `CORRELATED INCIDENT` log line
once enough related events land inside the correlation window.

### Step 6 — Run unit tests for the correlation logic
```bash
pytest tests/ -v
```

## 3. RabbitMQ topology

| Component | Name | Type | Notes |
|---|---|---|---|
| Exchange | `sentinel.raw_events` | topic | Member 2 publishes raw camera/sensor events here |
| Exchange | `sentinel.processed_events` | topic | Member 3 publishes normalized + correlated events here |
| Exchange | `sentinel.raw_events.dlx` | fanout | Dead-letter exchange for poison messages |
| Queue | `event_processing.raw` | — | Bound to `sentinel.raw_events` with routing key `#`, consumed by Member 3 |
| Queue | `event_processing.dlq` | — | Bound to the DLX, holds messages that failed processing after retries |
| Queue | `dashboard.processed` | — | Bound to `sentinel.processed_events` with `#` (Member 4 consumes) |
| Queue | `ai_analytics.processed` | — | Bound to `sentinel.processed_events` with `#` (Member 6 consumes) |

Routing key convention: `<source_type>.<event_type>`, e.g. `camera.motion_detected`,
`sensor.door_opened`. Processed events use `normalized.<event_type>` or
`correlated.<incident_type>`.

## 4. Correlation logic (summary)

Each normalized event is dropped into a **per-zone sliding time window**
(default 30s, configurable in `config/config.yaml`). On every new event, the
engine re-evaluates the events currently in that zone's window against a set
of rules (see `src/correlation_engine.py`):

1. **Intrusion suspected** — a `motion_detected` + `door_opened`/`line_crossing`
   in the same zone within the window, with no matching `access_granted`
   event → raises a `correlated.intrusion_suspected` incident.
2. **Loitering** — 3+ `motion_detected` events from the same camera in the
   window with no `face_detected` match → `correlated.loitering_suspected`.
3. **Tailgating** — an `access_granted` event followed by `line_crossing`
   count > 1 within a few seconds → `correlated.tailgating_suspected`.
4. **Confidence scoring** — each incident's `confidence` is the max of its
   contributing events' confidence, boosted (+0.1, capped at 1.0) for each
   additional corroborating event type.

See the full details and thresholds inline in `correlation_engine.py`.
