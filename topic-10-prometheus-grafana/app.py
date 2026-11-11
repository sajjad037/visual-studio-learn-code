"""Demo FastAPI app for the Prometheus + Grafana walkthrough.

Three endpoints, each built to move one dashboard signal:
  GET /      instant JSON          -> the healthy baseline (Rate)
  GET /slow  sleeps, then JSON     -> moves Duration (p95)
  GET /boom  returns HTTP 500      -> moves Errors
"""

import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Demo Shop API")

# The whole integration: instrument the app, expose /metrics.
Instrumentator().instrument(app).expose(app)


@app.get("/")
async def home():
    return {"status": "ok", "service": "demo-shop"}


@app.get("/slow")
async def slow():
    await asyncio.sleep(0.8)
    return {"status": "ok", "detail": "that took a while"}


@app.get("/boom")
async def boom():
    return JSONResponse(status_code=500, content={"detail": "something broke"})
