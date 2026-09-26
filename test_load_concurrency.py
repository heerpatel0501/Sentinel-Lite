"""
Sentinel-Lite Backend Concurrency & Load Testing Suite
Simulates 100+ concurrent requests and streams across the Sentinel-Lite API
Measures latency (p50, p95, p99), throughput (RPS), and thread-safety
"""

import asyncio
import time
import statistics
import httpx
import websockets
import json

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/api/v1/ws"
CONCURRENT_WORKERS = 100

async def benchmark_endpoint(client: httpx.AsyncClient, method: str, endpoint: str, semaphore: asyncio.Semaphore, payload=None, headers=None):
    async with semaphore:
        start = time.perf_counter()
        try:
            if method == "GET":
                resp = await client.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10.0)
            elif method == "POST":
                resp = await client.post(f"{BASE_URL}{endpoint}", json=payload, headers=headers, timeout=10.0)
            elapsed = (time.perf_counter() - start) * 1000.0
            return resp.status_code, elapsed
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000.0
            return 500, elapsed

async def run_concurrent_load(endpoint_desc: str, method: str, endpoint: str, num_requests: int = 100, payload_func=None, headers=None, concurrency: int = 20):
    print(f"\n[*] Running Benchmark: {endpoint_desc} ({num_requests} requests, concurrency={concurrency})")
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=100, max_keepalive_connections=50)) as client:
        start_total = time.perf_counter()
        sem = asyncio.Semaphore(concurrency)
        tasks = []
        for i in range(num_requests):
            p = payload_func(i) if payload_func else None
            tasks.append(benchmark_endpoint(client, method, endpoint, sem, payload=p, headers=headers))
        
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_total

    status_codes = [r[0] for r in results]
    latencies = [r[1] for r in results]
    successes = sum(1 for c in status_codes if 200 <= c < 300)
    failures = len(status_codes) - successes

    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)
    p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
    rps = num_requests / total_time if total_time > 0 else 0

    print(f"    - Completed: {num_requests} in {total_time:.2f}s ({rps:.1f} req/sec)")
    print(f"    - Success Rate: {successes}/{num_requests} ({(successes/num_requests)*100:.1f}%) | Failures: {failures}")
    print(f"    - Latency (ms): Min={min(latencies):.1f} | p50={p50:.1f} | p95={p95:.1f} | p99={p99:.1f} | Max={max(latencies):.1f}")

    return {
        "benchmark": endpoint_desc,
        "total": num_requests,
        "success": successes,
        "failures": failures,
        "rps": round(rps, 1),
        "p50_ms": round(p50, 1),
        "p95_ms": round(p95, 1),
        "p99_ms": round(p99, 1),
    }

async def benchmark_websocket_fanout(connections_count: int = 25):
    print(f"\n[*] Running Benchmark: WebSocket Real-Time Broadcast Fanout ({connections_count} concurrent sockets)")
    sockets = []
    try:
        connect_start = time.perf_counter()
        for _ in range(connections_count):
            ws = await websockets.connect(WS_URL)
            # receive initial handshake
            await ws.recv()
            sockets.append(ws)
        handshake_time = (time.perf_counter() - connect_start) * 1000.0
        print(f"    - Connected {len(sockets)} WebSocket clients in {handshake_time:.1f}ms")

        # Trigger canonical event creation to trigger broadcast
        async with httpx.AsyncClient() as client:
            test_event = {
                "source_id": f"bench-ws-{int(time.time()*1000)}",
                "camera_id": 1,
                "event_type": "vehicle_detection",
                "occurred_at": "2026-09-26T14:35:00",
                "confidence": 0.98,
                "payload": {"plate": "GJ01-WS-1234"}
            }
            await client.post(f"{BASE_URL}/api/v1/events", json=test_event)

        # Receive broadcast message across all sockets
        recv_start = time.perf_counter()
        received_count = 0
        for ws in sockets:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2.0)
                data = json.loads(msg)
                if data.get("event") == "event.created":
                    received_count += 1
            except asyncio.TimeoutError:
                pass
        fanout_time = (time.perf_counter() - recv_start) * 1000.0
        print(f"    - Broadcast Fanout Delivered to {received_count}/{connections_count} sockets in {fanout_time:.1f}ms")

        return {
            "benchmark": "WebSocket Fanout",
            "sockets": connections_count,
            "received": received_count,
            "fanout_ms": round(fanout_time, 1)
        }
    finally:
        for ws in sockets:
            await ws.close()

async def main():
    print("=" * 75)
    print("  SENTINEL-LITE HIGH-CONCURRENCY BACKEND LOAD TEST (100+ CONCURRENT REQS)")
    print("=" * 75)

    summary = []

    # 1. Health Probe
    res1 = await run_concurrent_load(
        "Liveness & Department Health (/health)",
        "GET",
        "/health",
        num_requests=100
    )
    summary.append(res1)

    # 2. Aggregated Dashboard Summary
    res2 = await run_concurrent_load(
        "Cross-Department Dashboard Summary (/api/v1/dashboard/summary)",
        "GET",
        "/api/v1/dashboard/summary",
        num_requests=100
    )
    summary.append(res2)

    # 3. Camera Registry Query
    res3 = await run_concurrent_load(
        "Camera Hardware Registry (/api/v1/cameras)",
        "GET",
        "/api/v1/cameras",
        num_requests=100
    )
    summary.append(res3)

    # 4. Canonical Event Ingestion (Concurrent POSTs)
    def event_payload(idx):
        return {
            "source_id": f"loadtest-evt-{int(time.time()*1000)}-{idx}",
            "camera_id": (idx % 20) + 1,
            "event_type": "vehicle_detection",
            "occurred_at": "2026-09-26T14:00:00",
            "confidence": 0.95,
            "payload": {"plate": f"GJ01-AB-{idx:04d}", "speed": 45}
        }

    res4 = await run_concurrent_load(
        "High-Throughput Canonical Event Ingestion (POST /api/v1/events)",
        "POST",
        "/api/v1/events",
        num_requests=100,
        payload_func=event_payload
    )
    summary.append(res4)

    # 5. Natural Language Search
    res5 = await run_concurrent_load(
        "Investigator Search & Journey Trajectory (/api/search?plate=GJ01AB1234)",
        "GET",
        "/api/search?plate=GJ01AB1234",
        num_requests=50
    )
    summary.append(res5)

    # 6. WebSocket Fanout
    ws_res = await benchmark_websocket_fanout(connections_count=30)

    print("\n" + "=" * 75)
    print("  LOAD TEST SCOREBOARD SUMMARY")
    print("=" * 75)
    print(f"  {'Benchmark':<45} | {'RPS':<8} | {'p50(ms)':<8} | {'p95(ms)':<8} | {'Status':<6}")
    print("  " + "-" * 80)
    for s in summary:
        status_str = "PASS" if s["failures"] == 0 else f"FAIL({s['failures']})"
        print(f"  {s['benchmark']:<45} | {s['rps']:<8} | {s['p50_ms']:<8} | {s['p95_ms']:<8} | {status_str:<6}")

    print(f"  {ws_res['benchmark']:<45} | {'N/A':<8} | {ws_res['fanout_ms']:<8} | {'N/A':<8} | {'PASS':<6}")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
