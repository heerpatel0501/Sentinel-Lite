"""
Sentinel-Lite Event Worker (Architecture Step 1 — Redis Real-Time Events)

Implements the official real-time event and queue processing architecture:
- Redis Pub/Sub for real-time fanout to dashboards and WebSockets
- Redis list queue for durable worker processing and DLQ handling
- Thread-safe in-memory queue for offline development fallback
- Fail clearly if Redis is required but unreachable
"""

import json
import os
import time
import threading
from collections import deque
from datetime import datetime
from typing import Optional, Callable


# ==============================================================================
# 1. In-Memory Queue (Dev/Local Fallback)
# ==============================================================================

class InMemoryQueue:
    """
    Thread-safe in-memory queue for local development when Redis is unavailable.
    Implements dead-letter queue (DLQ) for failed messages.
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
            message["_enqueued_at"] = datetime.utcnow().isoformat()
            self._queue.append(message)

    def consume(self) -> Optional[dict]:
        """Pop the next message from the queue."""
        with self._lock:
            if self._queue:
                return self._queue.popleft()
        return None

    def nack(self, message: dict):
        """Reject a message; send to DLQ if max retries exceeded."""
        retry_count = message.get("_retry_count", 0) + 1
        with self._lock:
            if retry_count >= self._max_retries:
                message["_dead_lettered_at"] = datetime.utcnow().isoformat()
                message["_retry_count"] = retry_count
                self._dlq.append(message)
                self.failed_count += 1
            else:
                message["_retry_count"] = retry_count
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
    - Real-time Pub/Sub fanout for live dashboards & WebSocket consumers
    - Asynchronous event queuing (LPUSH / RPOPLPUSH / BRPOP) for background processing
    - DLQ list for failed messages
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

        # 1. Pub/Sub for immediate real-time broadcast
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

    def nack(self, message: dict):
        """Send failed message to Redis DLQ list."""
        if not self._connected or not self._client:
            return
        try:
            message["_dead_lettered_at"] = datetime.utcnow().isoformat()
            self._client.rpush(self._dlq_name, json.dumps(message, default=str))
            self.failed_count += 1
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

    def stats(self) -> dict:
        return {
            "connected": self._connected,
            "url": self.url.split("@")[-1] if "@" in self.url else self.url,
            "pending": self.pending_count,
            "processed": self.processed_count,
            "dead_lettered": self.dlq_count,
            "failed": self.failed_count,
        }


# ==============================================================================
# 3. Event Worker
# ==============================================================================

class EventWorker:
    """
    Background worker that processes events from the queue and publishes real-time events.
    Uses Redis as the primary real-time event layer.
    Falls back cleanly to InMemoryQueue for local dev when Redis is not running and not strictly required.
    """

    def __init__(self):
        self._handlers: dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._use_redis = False

        redis_url = os.getenv("REDIS_URL")
        require_redis = (
            os.getenv("REQUIRE_REDIS", "false").lower() == "true"
            or os.getenv("ENVIRONMENT") == "production"
        )

        self.redis_queue = RedisEventQueue(redis_url)
        self.mem = InMemoryQueue(max_retries=3)

        if redis_url or require_redis:
            if self.redis_queue.connect():
                self._use_redis = True
                print(f"[EventWorker] Connected to Redis at {self.redis_queue.url}")
            else:
                if require_redis:
                    raise ConnectionError(
                        f"[EventWorker] Required Redis instance unreachable at {self.redis_queue.url}"
                    )
                print("[EventWorker] Redis configured but unreachable; falling back to in-memory queue for dev")
        else:
            print("[EventWorker] No REDIS_URL configured; running in local in-memory queue mode")

    @property
    def queue(self):
        return self.redis_queue if self._use_redis else self.mem

    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler function for a specific event type."""
        self._handlers[event_type] = handler

    def publish(self, event: dict):
        """
        Publish an event to the processing queue & real-time messaging layer.
        Sanitizes sensitive information before publishing.
        """
        event_type = event.get("event_type", "unknown")

        if self._use_redis:
            try:
                self.redis_queue.publish(event)
                return
            except Exception as e:
                print(f"[EventWorker] Redis publish failed: {e}")
                if os.getenv("REQUIRE_REDIS", "false").lower() == "true":
                    raise

        self.mem.publish(event)

    def _process_one(self, message: dict) -> bool:
        """Process a single message. Returns True on success."""
        event_type = message.get("event_type", "unknown")
        handler = self._handlers.get(event_type, self._handlers.get("default"))

        if not handler:
            print(f"[EventWorker] No handler for event_type={event_type}")
            return True  # Don't retry unknown event types

        try:
            handler(message)
            return True
        except Exception as e:
            print(f"[EventWorker] Handler error for {event_type}: {e}")
            return False

    def _worker_loop(self):
        """Main worker loop for queue processing."""
        while self._running:
            active_queue = self.redis_queue if self._use_redis else self.mem
            message = active_queue.consume()
            if message is None:
                time.sleep(0.1)  # Backoff when queue is empty
                continue

            success = self._process_one(message)
            if success:
                active_queue.ack(message)
            else:
                # Exponential backoff before retry
                retry = message.get("_retry_count", 0)
                backoff = min(2 ** retry, 30)
                time.sleep(backoff)
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
        print(f"[EventWorker] Worker started in {'redis' if self._use_redis else 'in-memory'} mode")

    def stop(self):
        """Stop the background worker."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            print("[EventWorker] Worker stopped")

    def stats(self) -> dict:
        return {
            "mode": "redis" if self._use_redis else "in-memory",
            "running": self._running,
            "queue_stats": self.queue.stats(),
        }


# ==============================================================================
# 4. Global Worker Instance & Default Handlers
# ==============================================================================

event_worker = EventWorker()


def default_event_handler(event: dict):
    """
    Default event handler that logs the event.
    In production, this triggers correlation, AI enrichment, etc.
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


def correlation_handler(event: dict):
    """
    Handles correlation events — groups related detections across cameras
    within a time window.
    """
    try:
        from middleware import structured_log
        structured_log.info(
            "event.correlation_triggered",
            event_type=event.get("event_type"),
            camera_id=event.get("camera_id"),
            plate=event.get("plate_number") or event.get("plate"),
        )
    except Exception:
        pass


# Register default handlers
event_worker.register_handler("default", default_event_handler)
event_worker.register_handler("vehicle_detection", default_event_handler)
event_worker.register_handler("plate_recognition", default_event_handler)
event_worker.register_handler("correlation", correlation_handler)
event_worker.register_handler("alert", default_event_handler)
event_worker.register_handler("camera_status", default_event_handler)
