# Topic 14 — Dockerize a FastAPI App: Dockerfile to Running Container

Companion code for the Visual Studio Learn video and blog post
"Dockerize a FastAPI App: Dockerfile to Running Container".

A tiny FastAPI notes API, packed two ways: a naive Dockerfile (1.65 GB image)
and a two-stage slim Dockerfile (198 MB) — same app, same answers.

## Files

| File | What it is |
|---|---|
| `main.py` | The app: a notes API with `GET /health`, `GET /notes`, `POST /notes` |
| `requirements.txt` | fastapi + uvicorn |
| `Dockerfile.naive` | The obvious first try: full `python:3.12`, everything copied in |
| `Dockerfile` | The proper pack: two stages on `python:3.12-slim`, non-root user, health check |
| `.dockerignore` | Keeps caches, git history and the recipes themselves out of the build context |
| `docker-compose.yml` | The everyday workflow: build + image name + port in six lines |

## Run it — the naive way

```bash
docker build -f Dockerfile.naive -t notes-api:naive .
docker run -d --name notes -p 8000:8000 notes-api:naive
curl http://localhost:8000/health
# {"status":"ok"}
docker images        # notes-api:naive ≈ 1.65 GB
docker rm -f notes
```

## Run it — the slim way

```bash
docker build -t notes-api:slim .
docker images        # notes-api:slim ≈ 198 MB
```

## Run it — the everyday way (compose)

```bash
docker compose up -d
docker compose ps    # the app reports (healthy)
curl http://localhost:8000/health
curl http://localhost:8000/notes
curl -X POST http://localhost:8000/notes -H "Content-Type: application/json" -d '{"text":"Docker works"}'
docker compose down
```

## Scan it

```bash
# Trivy: https://trivy.dev (install from the official apt repo)
trivy image --severity HIGH,CRITICAL notes-api:slim    # 51 findings when recorded
trivy image --severity HIGH,CRITICAL notes-api:naive   # 505 findings when recorded
```

Measured on the recording machine (Docker 29.1.3, 2026-11-18):
`python:3.12` = 1.62 GB · `python:3.12-slim` = 179 MB ·
`notes-api:naive` = 1.65 GB · `notes-api:slim` = 198 MB.
Your numbers will be close, not identical — base images change over time.
