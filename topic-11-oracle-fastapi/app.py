"""DevShelf — a small FastAPI app backed by Oracle AI Database.

The connection pool is created ONCE in the FastAPI lifespan (startup) and
closed on shutdown. Every request borrows a connection through a dependency
and gives it back. Credentials come from environment variables (see
connect_test.py for the full list).
"""
import os
from contextlib import asynccontextmanager

import oracledb
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

WALLET_DIR = os.environ["ORACLE_WALLET_DIR"]

POOL_PARAMS = dict(
    user=os.environ["ORACLE_USER"],
    password=os.environ["ORACLE_PASSWORD"],
    dsn=os.environ.get("ORACLE_DSN", "vsldb_tp"),
    config_dir=WALLET_DIR,
    wallet_location=WALLET_DIR,
    wallet_password=os.environ["ORACLE_WALLET_PASSWORD"],
    min=2,
    max=5,
)
if os.environ.get("ORACLE_PROXY_HOST"):
    POOL_PARAMS["https_proxy"] = os.environ["ORACLE_PROXY_HOST"]
    POOL_PARAMS["https_proxy_port"] = int(os.environ.get("ORACLE_PROXY_PORT", "8899"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = oracledb.create_pool_async(**POOL_PARAMS)
    print("Pool created (min 2, max 5)")
    yield
    await app.state.pool.close()
    print("Pool closed")


app = FastAPI(title="DevShelf", lifespan=lifespan)


async def get_connection():
    async with app.state.pool.acquire() as connection:
        yield connection


class ItemIn(BaseModel):
    title: str
    url: str
    tag: str | None = None


@app.get("/health")
async def health(connection=Depends(get_connection)):
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT 'ok' FROM DUAL")
        (status,) = await cursor.fetchone()
    return {"status": status}


@app.post("/items", status_code=201)
async def add_item(item: ItemIn, connection=Depends(get_connection)):
    async with connection.cursor() as cursor:
        new_id = cursor.var(oracledb.NUMBER)
        await cursor.execute(
            "INSERT INTO shelf_items (title, url, tag) VALUES (:1, :2, :3) RETURNING id INTO :4",
            [item.title, item.url, item.tag, new_id],
        )
        await connection.commit()
    return {"id": int(new_id.getvalue()[0]), **item.model_dump()}


@app.get("/items")
async def list_items(connection=Depends(get_connection)):
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT id, title, url, tag FROM shelf_items ORDER BY id")
        rows = await cursor.fetchall()
    return [{"id": r[0], "title": r[1], "url": r[2], "tag": r[3]} for r in rows]


@app.get("/items/{item_id}")
async def get_item(item_id: int, connection=Depends(get_connection)):
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT id, title, url, tag FROM shelf_items WHERE id = :1", [item_id]
        )
        row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="item not found")
    return {"id": row[0], "title": row[1], "url": row[2], "tag": row[3]}
