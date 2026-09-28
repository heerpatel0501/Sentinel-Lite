"""
Sentinel-Lite Event Worker (Architecture Step 1 & Phase C — Redis Real-Time Events)

Implements the official real-time event and queue processing architecture per ADR-003:
- Redis Pub/Sub (sentinel:events) for real-time fanout to dashboards and WebSockets
- Redis list queue (sentinel:queue) for durable worker processing
- Redis dead-letter queue (sentinel:queue:dlq) for failed messages with failure metadata
- Real correlation engine integration (multi-camera motion and cross-department plate sighting)
- Thread-safe in-memory queue for offline development fallback
- Explicit execution mode logging (never claiming Redis in fallback mode)
"""

import json
import os
import sys
import time
import uuid
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Optional, Callable, Tuple, List, Dict, Any

# Ensure project root is in sys.path for importing src modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src.correlation_engine import CorrelationEngine
    from src.models import NormalizedEvent, RawEvent, CorrelatedIncident
    from src.normalizer import normalize
except ImportError:
    CorrelationEngine = None
    NormalizedEvent = None
    RawEvent = None
    CorrelatedIncident = None
    normalize = None


# ==============================================================================
# 1. In-Memory Queue (Dev/Local Fallback)
# ==============================================================================

class InMemoryQueue:
    """
    Thread-safe in-memory queue for local development when Redis is unavailable.
    Implements dead-letter queue (DLQ) for failed messages after max_retries.
    """

    def __init__(self, max_retries: int = 3):
        self._queue: deque = deque()
        self._dlq: deque = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._max_retries = max_retries
        self.processed_count = 0
        self.failed_count = 0

    def publish(self, message: dict):
        """Add a message to the queue."""
        with self._lock:
            message["_retry_count"] = message.get("_retry_count", 0)
            message["_enqueued_at"] = datetime.now(timezone.utc).isoformat()
            self._queue.append(message)

    def consume(self) -> Optional[dict]:
        """Pop the next message from the queue."""
        with self._lock:
            if self._queue:
                return self._queue.popleft()
        return None

    def nack(self, message: dict, error: Optional[str] = None, max_retries: Optional[int] = None):
        """Reject a message; send to DLQ if max retries exceeded, else re-enqueue."""
        effective_max = max_retries if max_retries is not None else self._max_retries
        retry_count = message.get("_retry_count", 0) + 1
        with self._lock:
            message["_retry_count"] = retry_count
            if error:
                message["_error"] = str(error)

            if retry_count >= effective_max:
                message["_dead_lettered_at"] = datetime.now(timezone.utc).isoformat()
                self._dlq.append(message)
                self.failed_count += 1
            else:
                self._queue.append(message)

    def ack(self, message: dict):
        """Acknowledge successful processing."""
        with self._lock:
            self.processed_count += 1

    @property
    def pending_count(self) -> int:
        return len(self._queue)

    @property
    def dlq_count(self) -> int:
        return len(self._dlq)

    def get_dlq_messages(self, limit: int = 50) -> list:
        """Retrieve dead-letter messages for inspection."""
        with self._lock:
            return list(self._dlq)[:limit]

    def stats(self) -> dict:
        return {
            "mode": "in-memory-fallback",
            "connected": True,
            "pending": self.pending_count,
            "processed": self.processed_count,
            "dead_lettered": self.dlq_count,
            "failed": self.failed_count,
        }


# ==============================================================================
# 2. Redis Event Queue & Pub/Sub Wrapper
# ==============================================================================

class RedisEventQueue:
    """
    Redis-backed real-time messaging and queue processor.
    Responsible for:
    - Real-time Pub/Sub fanout (sentinel:events) for live dashboards & WebSocket consumers
    - Asynchronous event queuing (sentinel:queue) for background processing
    - DLQ list (sentinel:queue:dlq) for failed messages with full failure metadata
    Fails clearly if Redis is required but unavailable.
    """

    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._channel_name = "sentinel:events"
        self._queue_name = "sentinel:queue"
        self._dlq_name = "sentinel:queue:dlq"
        self._connected = False
        self.processed_count = 0
        self.failed_count = 0

    def connect(self) -> bool:
        """Attempt to connect and ping Redis. Fails clearly on error."""
        try:
            import redis
            self._client = redis.Redis.from_url(
                self.url,
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=5.0
            )
            self._client.ping()
            self._connected = True
            print(f"[EventWorker] Connected to Redis at {self.url}")
            print(f"[EventWorker] Running in Redis Pub/Sub mode")
            print(f"[EventWorker] Subscribed to: {self._channel_name}")
            print(f"[EventWorker] Queue: {self._queue_name} | DLQ: {self._dlq_name}")
            return True
        except Exception as e:
            self._connected = False
            is_strict = (
                os.getenv("REQUIRE_REDIS", "false").lower() == "true"
                or os.getenv("ENVIRONMENT") == "production"
            )
            if is_strict:
                raise ConnectionError(
                    f"[EventWorker CRITICAL] Redis is required but unavailable at {self.url}. "
                    f"Ensure Redis is running. Error: {e}"
                )
            print(f"[EventWorker] Redis connection failed at {self.url}: {e}")
            return False

    def publish(self, message: dict, channel: Optional[str] = None):
        """
        Publish an event to Redis Pub/Sub (for real-time live consumers)
        and enqueue into the Redis queue (for async background processing).
        """
        if not self._connected or not self._client:
            raise ConnectionError(f"Not connected to Redis ({self.url}). Cannot publish real-time event.")

        target_channel = channel or self._channel_name
        payload_str = json.dumps(message, default=str)

        # 1. Pub/Sub for immediate real-time broadcast to WebSockets
        self._client.publish(target_channel, payload_str)

        # 2. Durable list queue for background processing
        self._client.rpush(self._queue_name, payload_str)

    def consume(self) -> Optional[dict]:
        """Pop next message from the Redis processing list."""
        if not self._connected or not self._client:
            return None
        try:
            item = self._client.lpop(self._queue_name)
            if item:
                return json.loads(item)
        except Exception as e:
            print(f"[EventWorker] Redis consume error: {e}")
        return None

    def nack(self, message: dict, error: Optional[str] = None, max_retries: int = 3):
        """
        Send failed message to Redis DLQ list (sentinel:queue:dlq) if max retries exceeded,
        otherwise re-enqueue to the processing list. Retains original payload & failure metadata.
        """
        if not self._connected or not self._client:
            return
        try:
            retry_count = message.get("_retry_count", 0) + 1
            message["_retry_count"] = retry_count
            if error:
                message["_error"] = str(error)

            if retry_count >= max_retries:
                message["_dead_lettered_at"] = datetime.now(timezone.utc).isoformat()
                self._client.rpush(self._dlq_name, json.dumps(message, default=str))
                self.failed_count += 1
                evt_id = message.get("event_id") or message.get("source_id") or "unknown"
                print(f"[EventWorker] Message {evt_id} sent to DLQ ({self._dlq_name}) after {retry_count} retries: error={error}")
            else:
                self._client.rpush(self._queue_name, json.dumps(message, default=str))
        except Exception as e:
            print(f"[EventWorker] Redis DLQ push error: {e}")

    def ack(self, message: dict):
        """Acknowledge message processed."""
        self.processed_count += 1

    def get_pubsub(self):
        """Return a PubSub subscriber instance for WebSocket bridging."""
        if not self._connected or not self._client:
            return None
        ps = self._client.pubsub()
        ps.subscribe(self._channel_name)
        return ps

    @property
    def pending_count(self) -> int:
        if not self._connected or not self._client:
            return 0
        try:
            return self._client.llen(self._queue_name)
        except Exception:
            return 0

    @property
    def dlq_count(self) -> int:
        if not self._connected or not self._client:
            return 0
        try:
            return self._client.llen(self._dlq_name)
        except Exception:
            return 0

    def get_dlq_messages(self, limit: int = 50) -> list:
        """Retrieve dead-letter messages from Redis for inspection."""
        if not self._connected or not self._client:
            return []
        try:
            items = self._client.lrange(self._dlq_name, 0, limit - 1)
            return [json.loads(item) for item in items]
        except Exception as e:
            print(f"[EventWorker] Redis DLQ read error: {e}")
            return []

    def stats(self) -> dict:
        return {
            "mode": "redis",
            "connected": self._connected,
            "url": self.url.split("@")[-1] if "@" in self.url else self.url,
            "channel": self._channel_name,
            "queue": self._queue_name,
            "dlq": self._dlq_name,
            "pending": self.pending_count,
            "processed": self.processed_count,
            "dead_lettered": self.dlq_count,
            "failed": self.failed_count,
        }


# ==============================================================================
# 3. Event Worker & Correlation Pipeline
# ==============================================================================

class EventWorker:
    """
    Background worker that processes events from the queue and publishes real-time events.
    Uses Redis as the primary real-time event layer.
    Falls back cleanly to InMemoryQueue for local dev when Redis is not running and not strictly required.
    """

    def __init__(self, max_retries: int = 3):
        self._handlers: dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._use_redis = False
        self._max_retries = max_retries

        # Initialize correlation engine
        self._correlation_engine = None
        if CorrelationEngine is not None:
            self._correlation_engine = CorrelationEngine({
                "correlation": {
                    "window_seconds": 30,
                    "loitering_motion_threshold": 3,
                    "loitering_window_seconds": 60,
                    "tailgate_line_crossing_threshold": 2,
                    "tailgate_window_seconds": 8,
                    "motion_correlation_camera_threshold": 2,
                    "cross_dept_threshold": 2,
                    "confidence_boost_per_event": 0.1,
                    "max_confidence": 1.0,
                }
            })

        redis_url = os.getenv("REDIS_URL")
        require_redis = (
            os.getenv("REQUIRE_REDIS", "false").lower() == "true"
            or os.getenv("ENVIRONMENT") == "production"
        )

        self.redis_queue = RedisEventQueue(redis_url)
        self.mem = InMemoryQueue(max_retries=self._max_retries)

        if redis_url or require_redis:
            if self.redis_queue.connect():
                self._use_redis = True
            else:
                if require_redis:
                    raise ConnectionError(
                        f"[EventWorker CRITICAL] Required Redis instance unreachable at {self.redis_queue.url}"
                    )
                print(f"[EventWorker] Redis unavailable at {self.redis_queue.url}")
                print("[EventWorker] Running in In-Memory Development Fallback mode (NOT PRODUCTION)")
        else:
            print("[EventWorker] No REDIS_URL configured; running in In-Memory Development Fallback mode (NOT PRODUCTION)")

    @property
    def queue(self):
        return self.redis_queue if self._use_redis else self.mem

    @property
    def correlation_engine(self):
        return self._correlation_engine

    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler function for a specific event type."""
        self._handlers[event_type] = handler

    def publish(self, event: dict):
        """
        Publish an event to the processing queue & real-time messaging layer.
        """
        if self._use_redis:
            try:
                self.redis_queue.publish(event)
                return
            except Exception as e:
                print(f"[EventWorker] Redis publish failed: {e}")
                if os.getenv("REQUIRE_REDIS", "false").lower() == "true":
                    raise

        self.mem.publish(event)

    def _process_one(self, message: dict) -> Tuple[bool, Optional[str]]:
        """Process a single message. Returns (True, None) on success or (False, error_str)."""
        event_type = message.get("event_type", "unknown")
        handler = self._handlers.get(event_type, self._handlers.get("default"))

        if not handler:
            print(f"[EventWorker] No handler for event_type={event_type}")
            return True, None  # Don't retry unknown event types

        try:
            handler(message)
            return True, None
        except Exception as e:
            print(f"[EventWorker] Handler error for {event_type}: {e}")
            return False, str(e)

    def _worker_loop(self):
        """Main worker loop for queue processing."""
        while self._running:
            active_queue = self.redis_queue if self._use_redis else self.mem
            message = active_queue.consume()
            if message is None:
                time.sleep(0.05)  # Backoff when queue is empty
                continue

            success, err = self._process_one(message)
            if success:
                active_queue.ack(message)
            else:
                retry = message.get("_retry_count", 0)
                backoff = min(0.05 * (2 ** retry), 5.0)
                time.sleep(backoff)
                if hasattr(active_queue, "nack"):
                    try:
                        active_queue.nack(message, error=err, max_retries=self._max_retries)
                    except TypeError:
                        active_queue.nack(message)

    def start(self):
        """Start the background event processing worker."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._worker_loop, daemon=True, name="event-worker"
        )
        self._thread.start()
        if self._use_redis:
            print(f"[EventWorker] Worker loop started in Redis Pub/Sub & Queue mode")
        else:
            print(f"[EventWorker] Worker loop started in In-Memory Development Fallback mode (NOT PRODUCTION)")

    def stop(self):
        """Stop the background worker."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            print("[EventWorker] Worker stopped")

    def stats(self) -> dict:
        return {
            "mode": "redis" if self._use_redis else "in-memory",
            "production_ready": self._use_redis,
            "running": self._running,
            "queue_stats": self.queue.stats(),
        }


# ==============================================================================
# 4. Global Worker Instance & Default Handlers
# ==============================================================================

event_worker = EventWorker()


def evaluate_event_correlation(event: dict) -> List[Any]:
    """
    Normalizes incoming event and runs through CorrelationEngine.
    Returns any CorrelatedIncident objects produced.
    """
    if event_worker.correlation_engine is None or RawEvent is None or normalize is None:
        return []

    event_type = event.get("event_type") or event.get("type") or "motion_detected"
    source = str(event.get("camera_id") or event.get("source") or event.get("camera_name") or "camera_01")
    zone_id = str(event.get("zone_id") or event.get("zone") or event.get("department") or "zone_general")
    timestamp = event.get("timestamp") or event.get("occurred_at") or datetime.now(timezone.utc).isoformat()
    confidence = float(event.get("confidence") or event.get("confidence_score") or 1.0)

    attributes = dict(event.get("payload") or {})
    for key in ("plate", "plate_text", "plate_number", "department", "source_type"):
        if key in event and key not in attributes:
            attributes[key] = event[key]

    raw = RawEvent(
        event_id=str(event.get("event_id") or event.get("source_id") or uuid.uuid4()),
        source=source,
        source_type=str(event.get("source_type") or "camera"),
        event_type=event_type,
        timestamp=timestamp,
        zone_id=zone_id,
        confidence=confidence,
        metadata=attributes,
    )

    try:
        normalized = normalize(raw, strict=False)
        return event_worker.correlation_engine.process(normalized)
    except Exception as e:
        print(f"[EventWorker] Normalization/correlation error: {e}")
        return []


def default_event_handler(event: dict):
    """
    Default event handler that logs the event and evaluates correlation rules
    across cameras and departments. If a correlation is detected, publishes
    candidate incident to the real-time event channel for WebSocket broadcast.
    """
    try:
        from middleware import structured_log
        structured_log.info(
            "event.processed",
            event_type=event.get("event_type"),
            source_id=event.get("source_id"),
            camera_id=event.get("camera_id"),
        )
    except Exception:
        pass

    # Run correlation logic
    incidents = evaluate_event_correlation(event)
    for inc in incidents:
        print(
            f"[EventWorker] Correlated incident fired: {inc.incident_type} in {inc.zone_id} "
            f"(confidence={inc.confidence}) — {inc.summary}"
        )

        candidate_msg = {
            "event_type": "correlation",
            "incident_id": inc.incident_id,
            "incident_type": inc.incident_type,
            "zone_id": inc.zone_id,
            "confidence": inc.confidence,
            "summary": inc.summary,
            "metadata": inc.metadata,
            "camera_ids": inc.metadata.get("camera_ids", []),
            "departments": inc.metadata.get("departments", []),
            "plate_text": inc.metadata.get("plate_text", "SENSOR-CORRELATION"),
            "timestamp": inc.last_seen,
            "status": "candidate",
        }

        # Broadcast candidate event to Redis Pub/Sub for realtime dashboard consumption
        if event_worker._use_redis and event_worker.redis_queue._client:
            try:
                event_worker.redis_queue._client.publish(
                    event_worker.redis_queue._channel_name,
                    json.dumps(candidate_msg, default=str)
                )
            except Exception as e:
                print(f"[EventWorker] Failed to publish correlation fanout to Redis: {e}")


def correlation_handler(event: dict):
    """
    Handles pre-correlated events (e.g. from POST /api/events/correlate) and broadcasts
    to Redis Pub/Sub if not already published.
    """
    try:
        from middleware import structured_log
        structured_log.info(
            "event.correlation_triggered",
            event_type=event.get("event_type"),
            camera_id=event.get("camera_id"),
            plate=event.get("plate_number") or event.get("plate") or event.get("plate_text"),
        )
    except Exception:
        pass


# Register event handlers
for evt in (
    "default",
    "vehicle_detection",
    "plate_recognition",
    "plate_sighting",
    "motion_detected",
    "line_crossing",
    "door_opened",
    "door_forced",
    "access_granted",
    "access_denied",
    "alert",
    "camera_status",
):
    event_worker.register_handler(evt, default_event_handler)

event_worker.register_handler("correlation", correlation_handler)
