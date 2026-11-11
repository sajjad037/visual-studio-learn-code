"""Scripted load for the monitoring demo — a timeline, not a firehose.

Phases (each prints live counters once a second):
  1. baseline   ~5 req/s, only `/`              -> quiet dashboard
  2. burst      ~25 req/s mixed `/` + `/slow`   -> Rate spikes
  3. slow-heavy ~15 req/s, mostly `/slow`       -> Duration p95 climbs
  4. boom joins ~20 req/s with `/boom` mixed in -> Errors tick up

Usage:  python load_burst.py [phase_seconds]   (default 35s per phase)
        python load_burst.py --alert           (slow-heavy only, 100s,
                                                to trip the p95 alert)
"""

import asyncio
import collections
import sys
import time

import httpx

BASE = "http://localhost:8000"
counts = collections.Counter()
started = time.time()


async def worker(client: httpx.AsyncClient, path: str, interval: float, stop: float):
    while time.time() < stop:
        try:
            r = await client.get(BASE + path)
            counts[f"{path} -> {r.status_code}"] += 1
        except Exception:
            counts[f"{path} -> ERR"] += 1
        await asyncio.sleep(interval)


async def phase(name: str, seconds: int, mix: list[tuple[str, float]]):
    print(f"\n=== {name} ({seconds}s) ===", flush=True)
    stop = time.time() + seconds
    async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
        tasks = [asyncio.create_task(worker(client, p, iv, stop)) for p, iv in mix]
        while time.time() < stop:
            done = sum(counts.values())
            rate = done / max(1, time.time() - started)
            print(f"  t+{time.time() - started:5.0f}s  total={done:5d}  avg={rate:4.1f} req/s  "
                  + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())), flush=True)
            await asyncio.sleep(2)
        await asyncio.gather(*tasks, return_exceptions=True)


async def main():
    if "--alert" in sys.argv:
        # ~12 concurrent slow callers keep p95 pinned above 0.5s.
        await phase("ALERT RUN — /slow heavy", 100,
                    [("/slow", 0.85)] * 10 + [("/", 0.5)] * 2)
        return
    secs = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    await phase("PHASE 1 — baseline", secs, [("/", 0.2)])
    await phase("PHASE 2 — burst", secs, [("/", 0.08)] * 2 + [("/slow", 0.9)] * 4)
    await phase("PHASE 3 — slow-heavy", secs, [("/slow", 0.85)] * 8 + [("/", 0.3)])
    await phase("PHASE 4 — boom joins", secs,
                [("/", 0.1)] * 2 + [("/slow", 0.9)] * 4 + [("/boom", 0.4)] * 2)
    print(f"\nDone. Final counts: {dict(counts)}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
