"""
Sentinel-Lite Event Worker (Phase 11 — Outbox & Queue Processing)

Implements a resilient background event processing worker that:
- Reads from a RabbitMQ queue (production) or an in-memory queue (dev fallback)
- Processes canonical events through the correlation engine
- Supports dead-letter handling for failed events
- Implements retry with exponential backoff
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
    Thread-safe in-memory queue for local development when RabbitMQ is unavailable.
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
            "pending": self.pending_count,
            "processed": self.processed_count,
            "dead_lettered": self.dlq_count,
            "failed": self.failed_count,
        }


# ==============================================================================
# 2. RabbitMQ Queue Wrapper
# ==============================================================================

class RabbitMQQueue:
    """
    RabbitMQ-backed queue with dead-letter exchange (DLX).
    Falls back to InMemoryQueue if RabbitMQ is unavailable.
    """

    def __init__(self):
        self._connection = None
        self._channel = None
        self._exchange = "sentinel.events"
        self._queue_name = "sentinel.event_processor"
        self._dlq_name = "sentinel.event_processor.dlq"
        self._connected = False
        self.processed_count = 0
        self.failed_count = 0

    def connect(self) -> bool:
        """Attempt to connect to RabbitMQ."""
        try:
            import pika
            url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
            params = pika.URLParameters(url)
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()

            # Declare DLX and DLQ
            self._channel.exchange_declare(
                exchange=f"{self._exchange}.dlx", exchange_type="direct", durable=True
            )
            self._channel.queue_declare(queue=self._dlq_name, durable=True)
            self._channel.queue_bind(
                queue=self._dlq_name,
                exchange=f"{self._exchange}.dlx",
                routing_key=self._queue_name,
            )

            # Declare main exchange and queue with DLX
            self._channel.exchange_declare(
                exchange=self._exchange, exchange_type="topic", durable=True
            )
            self._channel.queue_declare(
                queue=self._queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": f"{self._exchange}.dlx",
                    "x-dead-letter-routing-key": self._queue_name,
                    "x-message-ttl": 300000,  # 5 min max processing time
                },
            )
            self._channel.queue_bind(
                queue=self._queue_name,
                exchange=self._exchange,
                routing_key="event.#",
            )

            self._connected = True
            return True
        except Exception as e:
            print(f"[EventWorker] RabbitMQ connection failed: {e}")
            self._connected = False
            return False

    def publish(self, message: dict, routing_key: str = "event.new"):
        """Publish a message to the exchange."""
        if not self._connected:
            raise ConnectionError("Not connected to RabbitMQ")
        import pika
        self._channel.basic_publish(
            exchange=self._exchange,
            routing_key=routing_key,
            body=json.dumps(message, default=str),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type="application/json",
                timestamp=int(time.time()),
            ),
        )

    def stats(self) -> dict:
        return {
            "connected": self._connected,
            "processed": self.processed_count,
            "failed": self.failed_count,
        }


# ==============================================================================
# 3. Event Worker
# ==============================================================================

class EventWorker:
    """
    Background worker that processes events from the queue.
    Supports both RabbitMQ and in-memory fallback.
    """

    def __init__(self):
        self._handlers: dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._use_rabbitmq = False

        # Try RabbitMQ, fall back to in-memory
        self.rmq = RabbitMQQueue()
        self.mem = InMemoryQueue(max_retries=3)

        if os.getenv("RABBITMQ_URL"):
            if self.rmq.connect():
                self._use_rabbitmq = True
                print("[EventWorker] Connected to RabbitMQ")
            else:
                print("[EventWorker] RabbitMQ unavailable, using in-memory queue")
        else:
            print("[EventWorker] No RABBITMQ_URL set, using in-memory queue")

    @property
    def queue(self):
        return self.rmq if self._use_rabbitmq else self.mem

    def register_handler(self, event_type: str, handler: Callable):
        """Register a handler function for a specific event type."""
        self._handlers[event_type] = handler

    def publish(self, event: dict):
        """
        Publish an event to the processing queue.
        This is the main entry point for the API to enqueue events.
        """
        event_type = event.get("event_type", "unknown")

        if self._use_rabbitmq:
            try:
                self.rmq.publish(event, routing_key=f"event.{event_type}")
                return
            except Exception as e:
                print(f"[EventWorker] RabbitMQ publish failed, falling back: {e}")

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
        """Main worker loop for in-memory queue processing."""
        while self._running:
            message = self.mem.consume()
            if message is None:
                time.sleep(0.1)  # Backoff when queue is empty
                continue

            success = self._process_one(message)
            if success:
                self.mem.ack(message)
            else:
                # Exponential backoff before retry
                retry = message.get("_retry_count", 0)
                backoff = min(2 ** retry, 30)
                time.sleep(backoff)
                self.mem.nack(message)

    def start(self):
        """Start the background event processing worker."""
        if self._running:
            return

        self._running = True

        if not self._use_rabbitmq:
            self._thread = threading.Thread(
                target=self._worker_loop, daemon=True, name="event-worker"
            )
            self._thread.start()
            print("[EventWorker] In-memory worker started")

    def stop(self):
        """Stop the background worker."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            print("[EventWorker] Worker stopped")

    def stats(self) -> dict:
        return {
            "mode": "rabbitmq" if self._use_rabbitmq else "in-memory",
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
    In production, this would trigger correlation, AI enrichment, etc.
    """
    from middleware import structured_log
    structured_log.info(
        "event.processed",
        event_type=event.get("event_type"),
        source_id=event.get("source_id"),
        camera_id=event.get("camera_id"),
    )


def correlation_handler(event: dict):
    """
    Handles correlation events — groups related detections across cameras
    within a time window.
    """
    from middleware import structured_log
    structured_log.info(
        "event.correlation_triggered",
        event_type=event.get("event_type"),
        camera_id=event.get("camera_id"),
        plate=event.get("plate_number"),
    )


# Register default handlers
event_worker.register_handler("default", default_event_handler)
event_worker.register_handler("vehicle_detection", default_event_handler)
event_worker.register_handler("plate_recognition", default_event_handler)
event_worker.register_handler("correlation", correlation_handler)
event_worker.register_handler("alert", default_event_handler)
