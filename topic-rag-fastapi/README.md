# Build a RAG App with FastAPI — Trailmark Outfitters catalogue assistant

The companion code for the Visual Studio Learn tutorial **"Build a RAG App with
FastAPI: Documents In, Grounded Answers Out"**.

A small, complete RAG (retrieval-augmented generation) app:

- **Documents** — a fictional shop catalogue: 5 plain markdown files in `catalogue/`
- **Chunks** — one section = one chunk (17 chunks)
- **Embeddings** — `all-MiniLM-L6-v2`, computed locally (384 numbers per chunk, no API key)
- **Store** — Chroma, on disk in `store/`
- **LLM** — Gemini, called from ONE function (`llm()` in `app.py`) — swap it for any model
- **Refusal** — if the nearest chunk is too far away, the app answers
  "I don't have that in the catalogue." instead of guessing

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=<your free AI Studio key>

python app.py ingest                     # build the store (re-run when documents change)
python app.py ask "How much are the Trail Runner Boots, and do they come in size 11?"
python app.py ask "Do you sell kayaks, and how much do they cost?"   # -> the refusal
python app.py compare "How do I send back a broken item?"           # keyword vs embedding search

uvicorn app:app --port 8023              # the same brain over HTTP
curl http://127.0.0.1:8023/health
curl -X POST http://127.0.0.1:8023/ask -H "Content-Type: application/json" \
     -d '{"question":"How much are the Trail Runner Boots, and do they come in size 11?"}'
```

## Try the stale-index lesson

Edit a price in `catalogue/products.md`, ask again — the answer does not change.
Run `python app.py ingest`, ask once more — now it does. In RAG, stale documents
in means stale answers out; re-indexing is part of the product.
