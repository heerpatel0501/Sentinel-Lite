"""
Sentinel-Lite Production Middleware Stack (Phase 11 Hardening)
- Request ID injection (X-Request-ID)
- Structured JSON access logging
- Security headers (OWASP)
- Rate limiting (in-memory sliding window)
- Request timing metrics
"""

import json
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

# ==============================================================================
# 1. Structured JSON Logger
# ==============================================================================

class StructuredLogger:
    """JSON-structured logger for production observability."""

    def __init__(self, name: str = "sentinel"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _log(self, level: str, event: str, **kwargs):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **kwargs,
        }
        self.logger.info(json.dumps(entry, default=str))

    def info(self, event: str, **kwargs):
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self._log("WARN", event, **kwargs)

    def error(self, event: str, **kwargs):
        self._log("ERROR", event, **kwargs)


structured_log = StructuredLogger("sentinel.access")


# ==============================================================================
# 2. Request ID Middleware
# ==============================================================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Injects a unique X-Request-ID into every request/response.
    If the client sends one, it is preserved for correlation.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ==============================================================================
# 3. Security Headers Middleware (OWASP)
# ==============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds OWASP-recommended security headers to every response:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: camera=(), microphone=(), geolocation=()
    - Cache-Control: no-store for API responses
    - Strict-Transport-Security for HTTPS environments
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        # API responses should not be cached
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        # HSTS for production (only if behind TLS terminator)
        if request.headers.get("X-Forwarded-Proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


# ==============================================================================
# 4. Structured Access Log Middleware
# ==============================================================================

class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Logs every request in structured JSON format with timing, status, and request ID.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Skip noisy health/ready probes from structured logs
        path = request.url.path
        if path not in ("/health", "/ready"):
            request_id = getattr(request.state, "request_id", "-")
            structured_log.info(
                "http.request",
                request_id=request_id,
                method=request.method,
                path=path,
                status=response.status_code,
                duration_ms=duration_ms,
                client=request.client.host if request.client else "-",
                user_agent=request.headers.get("User-Agent", "-")[:80],
            )

        response.headers["X-Response-Time-Ms"] = str(duration_ms)
        return response


# ==============================================================================
# 5. Rate Limiter Middleware (Sliding Window, In-Memory)
# ==============================================================================

class RateLimiter:
    """
    In-memory sliding window rate limiter.
    For production, swap with Redis-backed implementation.
    """

    def __init__(self, requests_per_minute: int = 120, burst_per_second: int = 30):
        self.rpm = requests_per_minute
        self.burst = burst_per_second
        self._minute_buckets: dict[str, list[float]] = defaultdict(list)
        self._second_buckets: dict[str, list[float]] = defaultdict(list)

    def _clean(self, bucket: list[float], window: float, now: float):
        """Remove entries older than window."""
        while bucket and bucket[0] < now - window:
            bucket.pop(0)

    def is_allowed(self, client_ip: str) -> tuple[bool, dict]:
        now = time.time()

        # Per-minute window
        minute_bucket = self._minute_buckets[client_ip]
        self._clean(minute_bucket, 60.0, now)

        # Per-second burst
        second_bucket = self._second_buckets[client_ip]
        self._clean(second_bucket, 1.0, now)

        remaining_minute = self.rpm - len(minute_bucket)
        remaining_burst = self.burst - len(second_bucket)

        headers = {
            "X-RateLimit-Limit": str(self.rpm),
            "X-RateLimit-Remaining": str(max(0, remaining_minute)),
            "X-RateLimit-Reset": str(int(now) + 60),
        }

        if remaining_minute <= 0 or remaining_burst <= 0:
            retry_after = 1 if remaining_burst <= 0 else 60
            headers["Retry-After"] = str(retry_after)
            return False, headers

        minute_bucket.append(now)
        second_bucket.append(now)
        return True, headers


_rate_limiter = RateLimiter(requests_per_minute=300, burst_per_second=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforces rate limiting per client IP.
    Exempts WebSocket upgrades and health probes.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Exempt health probes, WebSocket upgrades, and static files
        if path in ("/health", "/ready") or path.startswith("/evidence/"):
            return await call_next(request)

        # WebSocket upgrade requests
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        allowed, headers = _rate_limiter.is_allowed(client_ip)

        if not allowed:
            structured_log.warning(
                "rate_limit.exceeded",
                client=client_ip,
                path=path,
                method=request.method,
            )
            resp = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please retry after the specified interval.",
                    "retry_after": headers.get("Retry-After", "60"),
                },
            )
            for k, v in headers.items():
                resp.headers[k] = v
            return resp

        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response


# ==============================================================================
# 6. Metrics Collector (In-Memory)
# ==============================================================================

class MetricsCollector:
    """
    Lightweight in-memory metrics collector for request counts and latency.
    Exposes data via /metrics endpoint.
    """

    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.status_counts: dict[int, int] = defaultdict(int)
        self.endpoint_counts: dict[str, int] = defaultdict(int)
        self.latency_sum_ms = 0.0
        self.latency_max_ms = 0.0
        self.latency_samples = 0
        self.ws_connections_total = 0
        self.start_time = time.time()

    def record(self, path: str, status: int, duration_ms: float):
        self.request_count += 1
        self.status_counts[status] += 1
        self.endpoint_counts[path] += 1
        self.latency_sum_ms += duration_ms
        self.latency_samples += 1
        if duration_ms > self.latency_max_ms:
            self.latency_max_ms = duration_ms
        if status >= 400:
            self.error_count += 1

    def snapshot(self) -> dict:
        uptime = time.time() - self.start_time
        avg_latency = (
            round(self.latency_sum_ms / self.latency_samples, 2)
            if self.latency_samples > 0
            else 0.0
        )
        return {
            "uptime_seconds": round(uptime, 1),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate_pct": round(
                (self.error_count / self.request_count * 100)
                if self.request_count > 0
                else 0.0,
                2,
            ),
            "avg_latency_ms": avg_latency,
            "max_latency_ms": round(self.latency_max_ms, 2),
            "status_codes": dict(self.status_counts),
            "top_endpoints": dict(
                sorted(
                    self.endpoint_counts.items(), key=lambda x: x[1], reverse=True
                )[:15]
            ),
            "ws_connections_total": self.ws_connections_total,
        }


metrics = MetricsCollector()


class MetricsMiddleware(BaseHTTPMiddleware):
    """Records request metrics for the /metrics endpoint."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0
        metrics.record(request.url.path, response.status_code, duration_ms)
        return response


# ==============================================================================
# 7. Registration Helper
# ==============================================================================

def register_production_middleware(app):
    """
    Registers the full production middleware stack on a FastAPI app.
    Order matters: outermost middleware runs first.
    Execution order (request): Metrics -> RateLimit -> RequestID -> SecurityHeaders -> AccessLog
    """
    # Innermost (runs last on request, first on response)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware)
    # Outermost (runs first on request, last on response)
    app.add_middleware(MetricsMiddleware)
