# App Service Info API — Deploy FastAPI to Azure App Service

Companion code for the Visual Studio Learn post and video
**"How Do I Deploy a FastAPI App to Azure App Service? Step by Step,
From Zero"**.

A one-file FastAPI app whose three endpoints exist to prove a
deployment worked — and to make configuration visible. Deploy it to
Azure App Service on the **free F1 tier ($0)**, watch it report its own
Azure hostname, then delete the resource group when you're done.
Redeploying takes the same few commands.

## What it does

- `GET /` → hello, plus **where the code is running**: it reads the
  `APP_ENVIRONMENT` app setting (default `"local"`) and
  `WEBSITE_HOSTNAME`, which App Service defines automatically. Locally
  the answer is `environment: "local"`, `hostname: "localhost"`; in
  Azure the same code answers `"production"` and the real
  `*.azurewebsites.net` hostname.
- `GET /health` → `{"status": "ok", "python": <version>, "utc_time":
  <now>}` — the endpoint you hit to prove the app is really up.
- `GET /greet/{name}` → a personalised greeting — proof that routing
  and path parameters survived the trip.

## Prerequisites

- **Python 3.12** (the tutorial uses Python 3.12.3; FastAPI 0.162.0
  supports 3.10–3.14).
- **Azure CLI 2.91.0** (the version current when the tutorial was
  recorded).
- An **Azure account** — the free account is enough; everything here
  runs on the free F1 tier.

Pinned versions: fastapi 0.162.0 · uvicorn 0.54.0 · gunicorn 26.2.0 ·
uvicorn-worker 0.4.0.

## Environment setup

### 1. Create the Azure free account (skip if you have one)

1. Go to **azure.microsoft.com/free** and choose **Try Azure for
   free**.
2. Sign in with a **Microsoft account or a GitHub account**.
3. Fill in the profile details.
4. **Identity verification**: a **phone number** and a **credit card
   or non-prepaid debit card**. The card is only checked — a
   **~$1 temporary authorization hold** may appear and is removed.
   You are charged nothing unless you later choose pay-as-you-go.
5. Accept the agreement and finish.

The offer, as documented by Microsoft: a **US$200 credit for your
first 30 days**, plus amounts of popular services free for 12 months
(and some always free). If you don't upgrade within 30 days or when
the credit runs out, the account is disabled until you do — nothing
keeps billing in the background. This tutorial never needs the credit:
the F1 plan is $0.

### 2. Install the Azure CLI and sign in

Install the Azure CLI for your operating system from Microsoft's
install page (learn.microsoft.com — "Install the Azure CLI"), then:

```bash
az --version        # expect azure-cli 2.91.0
az login
az account show     # confirm which subscription you are deploying to
```

### 3. Create the Python environment and run locally first

```bash
python3 -m venv .venv && source .venv/bin/activate   # macOS / Linux
# Windows PowerShell:  py -m venv .venv ; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/ — it answers `"environment": "local"`.
Also try `/health` and `/greet/YourName`. **Do not skip the local
run**: it separates "my code is broken" from "my deploy is broken"
before Azure is involved.

## The two files Azure cares about

- **`requirements.txt` must sit at the project root.** App Service's
  build looks for it there; without it the build reports *"Could not
  find setup.py or requirements.txt; Not running pip install."*
- **`startup.txt`** holds the startup command — on Python 3.13 and
  earlier, App Service auto-detects only Django and Flask. A FastAPI
  app with no startup command doesn't error; it silently serves a
  built-in default page. (Python 3.14+ auto-detects FastAPI; this
  tutorial pins 3.12 because the startup command is the skill every
  existing app still needs.) The command:

  ```
  gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 -k uvicorn_worker.UvicornWorker main:app --access-logfile '-' --error-logfile '-'
  ```

  Why each part: Gunicorn alone can't run an ASGI app (its default
  worker is a sync WSGI worker), so the **Uvicorn worker class** does
  the actual serving — from the `uvicorn-worker` package, because
  uvicorn 0.54.0 deprecates the old `uvicorn.workers` module. **Port
  8000** is the port the built-in Python image exposes. **2 workers**,
  not the 4 many tutorials show: the free F1 plan has 1 GB of RAM.
  Note what is *not* set: `WEBSITES_PORT` — that app setting is for
  custom containers, not the built-in images.

## Deploy (free tier only)

```bash
# 1. A resource group to hold everything (delete the group = delete all)
az group create --name fastapi-info-rg --location canadacentral

# 2. The FREE plan — the --sku F1 part is what keeps this at $0
az appservice plan create --name fastapi-info-plan \
  --resource-group fastapi-info-rg --sku F1 --is-linux \
  --location canadacentral

# 3. The web app on Python 3.12 (pick a globally unique <app-name>)
az webapp create --name <app-name> --resource-group fastapi-info-rg \
  --plan fastapi-info-plan --runtime "PYTHON:3.12"

# 4. App settings: build on deploy + tell the app where it lives
az webapp config appsettings set --name <app-name> \
  --resource-group fastapi-info-rg \
  --settings SCM_DO_BUILD_DURING_DEPLOYMENT=true APP_ENVIRONMENT=production

# 5. Zip the app — requirements.txt at the archive root,
#    and NO .venv, .git, or .env in the archive
zip deploy.zip main.py requirements.txt startup.txt

# 6. Deploy the zip
az webapp deploy --name <app-name> --resource-group fastapi-info-rg \
  --type zip --src-path deploy.zip
```

Set the startup command (portal: your web app → **Configuration** →
**General settings** → **Startup Command**, paste the line from
`startup.txt`, **Save**), then open
`https://<app-name>.azurewebsites.net/` — `/` now answers
`"environment": "production"` with your real hostname.

The shortcut version, for a fresh folder: **`az webapp up`** creates
the resource group, plan, and app and deploys in one command. The
post shows both; the long way is the one that teaches you what the
shortcut did.

Watch it work: `az webapp log config --name <app-name>
--resource-group fastapi-info-rg --web-server-logging filesystem`
once, then `az webapp log tail --name <app-name> --resource-group
fastapi-info-rg`.

## What it costs

**$0 on F1** — with real limits: 60 CPU minutes per day, 1 GB RAM,
1 GB storage, at most 10 apps per plan, no custom domains (the
`*.azurewebsites.net` name only), no Always On (the app unloads when
idle, so the first hit after a quiet spell is slow), and no SLA. The
first paid step up, B1 in Canada Central, was US$0.018/hour
(≈ US$13.14/month) when the tutorial was recorded (October 2026).
One billing warning from Microsoft's pricing page: plans are charged
while they exist, *including for stopped apps* — deleting is the
reliable off switch.

## Delete it when you're done

Everything lives in one resource group, so one command removes all
of it:

```bash
az group delete --name fastapi-info-rg --yes
```

That is what the tutorial itself does after filming. Nothing is lost:
this folder plus the commands above redeploy the app from scratch
any time.

## Errors you may hit

- **The site shows a default/placeholder page, not your app** —
  FastAPI wasn't detected (no startup command on Python ≤ 3.13) and
  App Service ran its built-in default app. Set the startup command,
  restart, wait ~20 seconds.
- **`TypeError: FastAPI.__call__() missing 1 required positional
  argument: 'send'`** in the log stream — Gunicorn's default sync
  worker met an ASGI app. The Uvicorn worker class in the startup
  command is the fix.
- **"Could not find setup.py or requirements.txt; Not running pip
  install."** — the dependency file isn't at the project/zip root.
  Move it and redeploy.
- **`ModuleNotFoundError` at startup** — the packages were never
  installed, usually because the build never ran or a local venv was
  deployed with the code. Set `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
  and redeploy; never ship your venv.
- **"Service Unavailable" / the first hit hangs** — a cold start: F1
  has no Always On, and Microsoft's docs warn the app "might take
  longer to start up when you use free tiers… and become responsive
  after you refresh". If it persists, read the log stream before
  changing anything.
- **The app stops responding part-way through the day** — the F1
  60-CPU-minutes-per-day quota is used up; it resets the next day.
  That's the free tier's ceiling working as designed.
- **A DeprecationWarning about `uvicorn.workers` in the logs** — not
  a failure: the class moved to the `uvicorn-worker` package. This
  repo already uses the new class; the warning appears if you follow
  an older tutorial's startup command.

## Next steps

Containerise this same app with Docker (Topic #9), deploy it on every
push with GitHub Actions via Deployment Center (Topic #13), and watch
it with Prometheus + Grafana (Topic #10) — the plan's ship-and-run
mini-series builds on this folder throughout.
