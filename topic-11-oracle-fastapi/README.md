# Connect FastAPI to Oracle Database — DevShelf

Companion code for the Visual Studio Learn tutorial
"Connect FastAPI to Oracle Database: 1 pip Install, a 5-Line Connection, and a Real Pool".

A small FastAPI app (**DevShelf** — it saves developer reference links) backed by
Oracle AI Database, using the **python-oracledb** driver in **Thin mode with a wallet**.
No Oracle Client / Instant Client install is needed anywhere.

## What each file does

| File | Step |
|---|---|
| `connect_test.py` | The five-line connection — prints the server version read back from the database itself |
| `setup_db.py` | Creates the `shelf_items` table and inserts three real rows |
| `app.py` | The FastAPI app: pool created once in the lifespan (min 2, max 5), closed on shutdown; `/health`, `POST /items`, `GET /items`, `GET /items/{id}` |
| `timing.py` | Measures one real query round trip (median of 15) |

## Before you run anything

1. Create an **Always Free Autonomous Database** in Oracle Cloud (free tier, no card charges).
2. Download its **wallet** from the console and **unzip it** — the driver reads the *folder*, not the zip.
3. Set the environment variables (never type secrets into code):

```bash
export ORACLE_USER=ADMIN
export ORACLE_PASSWORD=<your database password>
export ORACLE_WALLET_PASSWORD=<the wallet's own password — a DIFFERENT password>
export ORACLE_WALLET_DIR=/path/to/extracted/wallet
export ORACLE_DSN=<your alias from tnsnames.ora, e.g. vsldb_tp>
```

> The wallet password and the database password are two different passwords with two
> different jobs. Mixing them up is the most common wallet connection failure.

## Run it

```bash
pip install -r requirements.txt
python connect_test.py     # Connected — server version: ...
python setup_db.py         # table + 3 rows, read back
uvicorn app:app --port 8000
curl http://127.0.0.1:8000/items
python timing.py           # your own measured round trip
```

On a network that must egress through an HTTP proxy, set `ORACLE_PROXY_HOST` /
`ORACLE_PROXY_PORT` as well — the code passes them to the driver only when set.

## The one idea to keep

Start Thin, pool at startup, guard the wallet like a password, and place the app
beside the database — distance is the one cost no code can optimise away.
