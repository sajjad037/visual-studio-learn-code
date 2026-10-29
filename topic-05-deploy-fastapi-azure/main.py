"""App Service Info API: the smallest app that proves a deploy worked.

Companion code for the Visual Studio Learn post and video
"How Do I Deploy a FastAPI App to Azure App Service? Step by Step,
From Zero".

This one-file FastAPI app exists to make deployment concepts visible:

- GET /        reports where the code is running. It reads the
               APP_ENVIRONMENT app setting (which we set to
               "production" in Azure) and WEBSITE_HOSTNAME, a variable
               App Service defines automatically. Locally, with neither
               set, the same code answers "local" — the before/after
               contrast is the whole demo.
- GET /health  status, the Python version, and the current UTC time:
               the endpoint you hit to prove the app is really up.
- GET /greet/{name}
               a personalised greeting — proof that routing and path
               parameters survived the trip to the cloud.

Requires: Python 3.10 or newer and the packages in requirements.txt.
Run locally:  uvicorn main:app --reload
In Azure it is served by Gunicorn with the Uvicorn worker class — see
startup.txt, which holds the exact command the post sets in App
Service.
"""

import logging
import os
import platform
from datetime import datetime, timezone

from fastapi import FastAPI

logger = logging.getLogger("info_api")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

app = FastAPI(title="App Service Info API")


def environment() -> str:
    """Where this process believes it is running.

    APP_ENVIRONMENT is an ordinary app setting: unset locally (so the
    default "local" answers), set to "production" in Azure.
    """
    return os.environ.get("APP_ENVIRONMENT", "local")


def hostname() -> str:
    """The site's public hostname, when the platform provides one.

    App Service auto-defines WEBSITE_HOSTNAME for every web app.
    Locally it does not exist, so the honest answer is "localhost".
    """
    return os.environ.get("WEBSITE_HOSTNAME", "localhost")


@app.get("/")
def read_root() -> dict:
    """Say hello, and say where from — the deploy's proof page."""
    return {
        "app": "App Service Info API",
        "message": "Hello from FastAPI",
        "environment": environment(),
        "hostname": hostname(),
    }


@app.get("/health")
def health() -> dict:
    """Liveness plus runtime identity: status, Python version, UTC now."""
    return {
        "status": "ok",
        "python": platform.python_version(),
        "utc_time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/greet/{name}")
def greet(name: str) -> dict:
    """A greeting with the visitor's name — routing, proven live."""
    return {
        "greeting": f"Hello, {name}!",
        "environment": environment(),
        "hostname": hostname(),
    }
