# Topic #13 — CI/CD for a FastAPI App: GitHub Actions to Azure App Service

Companion code for the Visual Studio Learn post **"CI/CD for a FastAPI App — GitHub Actions to Azure App Service"** (https://visualstudiolearn.blogspot.com).

One workflow file does the whole pipeline: run the tests on every pull request, and deploy to Azure App Service only when code lands on `main`, after the tests pass, logging in with OIDC so no Azure password is ever stored in GitHub.

## What's in this folder

| File | What it is |
|---|---|
| `main.py` | The demo FastAPI app — three routes (`/`, `/health`, `/greet/{name}`), kept tiny on purpose |
| `requirements.txt` | Runtime pins: FastAPI 0.115.6, uvicorn, gunicorn, uvicorn-worker |
| `requirements-dev.txt` | Test pins: pytest 8.3.4, httpx |
| `tests/test_main.py` | Three tests, one per route — the same tests the pipeline runs |
| `.github/workflows/ci-cd.yml` | The workflow exactly as taught in the post: a `test` job and a `deploy` job gated by `needs: test` |
| `startup.txt` | The exact Azure App Service startup command (gunicorn + uvicorn worker) |

## Run it locally

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -v          # 3 passed
uvicorn main:app   # then open /, /health, /greet/Azure
```

## How the pipeline works

1. **Test job** — runs on every `pull_request` (and on push). It holds no secrets, so untrusted code has nothing to steal. A failing test puts a red cross on the pull request.
2. **Deploy job** — runs only on a push to `main` (`if:` guard) and only after the test job passes (`needs: test`). It logs in to Azure with OIDC (`azure/login@v2`) using three identifier secrets — `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` — plus an `AZURE_WEBAPP_NAME` variable, then deploys with `azure/webapps-deploy@v3`. The `permissions: id-token: write` line on the deploy job is what lets GitHub mint the OIDC token; the test job deliberately does not have it.

## One rule this code follows

Plain `pull_request`, never `pull_request_target`. `pull_request_target` runs in the base repository's context, with secrets and a write token, even for fork code — and from **December 2, 2026** GitHub blocks it by default in public repositories. Plain `pull_request` runs the proposed code with no secrets, which is exactly right for tests.

Versions used (November 2026): Python 3.12, FastAPI 0.115.6, pytest 8.3.4, actions/checkout@v4, actions/setup-python@v5, azure/login@v2, azure/webapps-deploy@v3.
