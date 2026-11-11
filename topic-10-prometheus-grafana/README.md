# Topic 10 — Monitor a FastAPI App with Prometheus + Grafana

Companion code for the Visual Studio Learn tutorial **"Monitor a FastAPI App with
Prometheus + Grafana (Metrics, Dashboards, Alerts)"**.

The demo app has one endpoint per dashboard signal:

| Endpoint   | Behaviour              | Signal it moves |
|------------|------------------------|-----------------|
| `GET /`    | instant JSON           | Rate (healthy baseline) |
| `GET /slow`| sleeps 0.8s, then JSON | Duration (p95) |
| `GET /boom`| HTTP 500, every time   | Errors (5xx share) |

## Files

- `app.py` — the FastAPI app, including the whole monitoring integration:
  `Instrumentator().instrument(app).expose(app)` (serves `/metrics`).
- `requirements.txt` — pinned versions (FastAPI 0.162.4, uvicorn 0.54.0,
  prometheus-fastapi-instrumentator 8.1.0, httpx 0.28.1).
- `prometheus.yml` — scrape config (job `fastapi` → `localhost:8000`, 5s interval
  for the demo; Prometheus's default is 1m).
- `load_burst.py` — the four-phase load script used to attack the app on camera
  (the filmed run made 2,285 requests).
- `dashboard.json` — the exported Grafana dashboard ("FastAPI — RED": Rate /
  Errors / Duration panels). Import it into Grafana and pick your Prometheus
  data source.
- `grafana-alert-rule.json` — the Grafana alert rule from the tutorial
  ("FastAPI p95 too high": overall p95 > 0.5s for 1m), as provisioned.
- `prometheus-alert-rules.yml` — the same alert as a Prometheus rule file,
  for setups that alert from Prometheus instead of Grafana.

## Run it

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --port 8000
# in another terminal: start Prometheus with prometheus.yml, then Grafana,
# add Prometheus (http://localhost:9090) as a data source, import dashboard.json
python load_burst.py
```

Versions used in the tutorial: Prometheus 3.16.0 · Grafana OSS 13.3.0 · Python 3.12.

## Things worth knowing before you copy this to a real app

- The instrumentator **groups status labels** (`5xx`, never `500`). Querying
  `status="500"` returns an empty result, not an error.
- Percentiles from `histogram_quantile` are **interpolated estimates** inside the
  histogram buckets (default `le` = 0.1, 0.5, 1.0, +Inf) — right for spotting the
  slow endpoint, not a stopwatch.
- The demo alert wires **no notification channel**; add a Grafana contact point
  (or a Prometheus Alertmanager) to get paged.
- Don't expose `/metrics` publicly without protection — it describes your app's
  internals.
