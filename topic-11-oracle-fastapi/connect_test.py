"""Step 5 — the five-line connection (python-oracledb, Thin mode + wallet).

Credentials come from environment variables — never type secrets into code:
  ORACLE_USER            database user (ADMIN for this demo)
  ORACLE_PASSWORD        database password (NOT the wallet password)
  ORACLE_WALLET_PASSWORD the wallet's own password (a different password)
  ORACLE_WALLET_DIR      folder the wallet zip was extracted to
  ORACLE_DSN             TNS alias from tnsnames.ora (default: vsldb_tp)
Optional, only on networks that must egress through an HTTP proxy:
  ORACLE_PROXY_HOST / ORACLE_PROXY_PORT
"""
import os

import oracledb

WALLET_DIR = os.environ["ORACLE_WALLET_DIR"]

extra = {}
if os.environ.get("ORACLE_PROXY_HOST"):
    extra["https_proxy"] = os.environ["ORACLE_PROXY_HOST"]
    extra["https_proxy_port"] = int(os.environ.get("ORACLE_PROXY_PORT", "8899"))

connection = oracledb.connect(
    user=os.environ["ORACLE_USER"],
    password=os.environ["ORACLE_PASSWORD"],
    dsn=os.environ.get("ORACLE_DSN", "vsldb_tp"),
    config_dir=WALLET_DIR,
    wallet_location=WALLET_DIR,
    wallet_password=os.environ["ORACLE_WALLET_PASSWORD"],
    **extra,
)

print("Connected — server version:", connection.version)
connection.close()
