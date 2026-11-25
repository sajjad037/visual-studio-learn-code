"""Step 12 — measure one real round trip: this machine -> VSLDB (Montreal).
Runs a one-line query over a pooled connection, N times; reports the median.
This measured number (and only this) fills the video's round-trip line."""
import asyncio
import os
import statistics
import time

import oracledb

WALLET_DIR = os.environ["ORACLE_WALLET_DIR"]
PARAMS = dict(
    user=os.environ["ORACLE_USER"],
    password=os.environ["ORACLE_PASSWORD"],
    dsn=os.environ.get("ORACLE_DSN", "vsldb_tp"),
    config_dir=WALLET_DIR,
    wallet_location=WALLET_DIR,
    wallet_password=os.environ["ORACLE_WALLET_PASSWORD"],
    min=1,
    max=2,
)
if os.environ.get("ORACLE_PROXY_HOST"):
    PARAMS["https_proxy"] = os.environ["ORACLE_PROXY_HOST"]
    PARAMS["https_proxy_port"] = int(os.environ.get("ORACLE_PROXY_PORT", "8899"))


async def main():
    pool = oracledb.create_pool_async(**PARAMS)
    samples = []
    async with pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT 1 FROM DUAL")  # warm-up
            await cursor.fetchone()
            for _ in range(15):
                t0 = time.perf_counter()
                await cursor.execute("SELECT 1 FROM DUAL")
                await cursor.fetchone()
                samples.append((time.perf_counter() - t0) * 1000)
    await pool.close()
    samples.sort()
    print("round trips (ms):", [round(s, 1) for s in samples])
    print(f"median round trip: {statistics.median(samples):.0f} ms")


asyncio.run(main())
