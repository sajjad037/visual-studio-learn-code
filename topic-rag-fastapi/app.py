#!/usr/bin/env python3
"""Build a RAG App with FastAPI — Trailmark Outfitters catalogue assistant.

RAG = retrieval-augmented generation. The pattern, end to end:
  1. DOCUMENTS  — plain markdown files in ./catalogue
  2. CHUNKS     — each file is cut into one-idea pieces
  3. EMBEDDINGS — a local MiniLM model turns every chunk into 384 numbers
                  that capture its meaning (no API key, no cost)
  4. STORE      — Chroma keeps the chunks + numbers on disk
  5. RETRIEVE   — a question is embedded the same way; the nearest
                  chunks come back
  6. PROMPT     — the chunks + the question + one strict rule
  7. ANSWER     — one swappable function (llm) asks the model; the app
                  refuses when the documents do not hold the answer

Run it:
  python app.py ingest                     # build / rebuild the store
  python app.py ask "your question"        # chunks + prompt + answer
  python app.py compare "your question"    # keyword vs embedding search
  uvicorn app:app --port 8023              # serve the same brain over HTTP
"""
import json
import os
import re
import sys

import chromadb
from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(HERE, "catalogue")
STORE_DIR = os.path.join(HERE, "store")
MODEL_NAME = "all-MiniLM-L6-v2"      # small, local, free — 384 numbers per text
TOP_K = 3
REFUSAL = "I don't have that in the catalogue."
# Lock 1 (in code): if even the NEAREST chunk is farther than this, the
# documents do not cover the question — refuse without calling the model.
# (Tuned from measured distances; see FACTS in the build notes.)
REFUSAL_DISTANCE = 1.05

_embedder = None


def embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder


def embed(texts):
    """Texts -> lists of 384 numbers each, computed locally by MiniLM."""
    return embedder().encode(texts, show_progress_bar=False).tolist()


# ---------------------------------------------------------------- documents
def load_chunks():
    """Cut every catalogue file into chunks: one section = one chunk.
    A heading-only block is glued onto the block that follows it."""
    chunks = []
    for fname in sorted(os.listdir(DOCS_DIR)):
        if not fname.endswith(".md"):
            continue
        raw = open(os.path.join(DOCS_DIR, fname)).read()
        blocks = [b.strip() for b in re.split(r"\n\s*\n", raw) if b.strip()]
        merged, pending = [], ""
        for b in blocks:
            if b.startswith("#") and "\n" not in b:   # bare heading line
                pending = b + "\n"
                continue
            merged.append(pending + b)
            pending = ""
        if pending:
            merged.append(pending)
        for i, text in enumerate(merged):
            chunks.append({"id": f"{fname}#{i}", "source": fname, "text": text})
    return chunks


def collection():
    client = chromadb.PersistentClient(path=STORE_DIR)
    return client.get_or_create_collection("catalogue")


def ingest():
    chunks = load_chunks()
    col = collection()
    col.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        embeddings=embed([c["text"] for c in chunks]),
        metadatas=[{"source": c["source"]} for c in chunks],
    )
    return chunks


# ---------------------------------------------------------------- retrieval
def retrieve(question, k=TOP_K):
    col = collection()
    res = col.query(query_embeddings=embed([question]), n_results=k)
    out = []
    for text, meta, dist in zip(res["documents"][0], res["metadatas"][0],
                                res["distances"][0]):
        out.append({"source": meta["source"], "text": text,
                    "distance": round(float(dist), 3)})
    return out


STOPWORDS = {"how", "do", "i", "a", "an", "the", "is", "are", "can", "you",
             "your", "what", "when", "where", "does", "it", "to", "of", "for",
             "in", "on", "and", "or", "me", "my", "we", "our"}


def keyword_search(question, k=TOP_K):
    """The old way: count shared content words. No meaning, just letters."""
    qwords = {w for w in re.findall(r"[a-z]+", question.lower())} - STOPWORDS
    scored = []
    for c in load_chunks():
        words = set(re.findall(r"[a-z]+", c["text"].lower()))
        scored.append({"source": c["source"], "text": c["text"],
                       "shared": sorted(qwords & words)})
    scored.sort(key=lambda r: -len(r["shared"]))
    return scored[:k]


# ---------------------------------------------------------------- the brain
def build_prompt(question, chunks):
    context = "\n\n".join(
        f"[{c['source']}]\n{c['text']}" for c in chunks)
    return f"""Answer the question using ONLY the context below.
If the answer is not in the context, reply with exactly:
{REFUSAL}
Keep the answer short and use the prices and facts as written.

CONTEXT:
{context}

QUESTION: {question}"""


def llm(prompt):
    """THE SWAPPABLE BRAIN — this one function is the only place a model
    is called. Swap Gemini for any other model by rewriting this body;
    the rest of the app never notices.
    Key: GEMINI_API_KEY from the environment (our build harness injects
    its registered credential the same way when no key is set)."""
    import requests
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        headers = {"x-goog-api-key": key}
    else:
        sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
        from dynamic_credentials import dynamic_credential_entry
        entry = dynamic_credential_entry("custom.gemini")
        headers = {entry["placement"]["custom_header"]:
                   str(entry["surrogate"]).strip()}
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           "gemini-3.8-flash:generateContent")
    r = requests.post(url, headers=headers, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 512},
    }, timeout=120, allow_redirects=False)
    r.raise_for_status()
    data = r.json()
    return "".join(p.get("text", "")
                   for p in data["candidates"][0]["content"]["parts"]).strip()


def ask(question):
    chunks = retrieve(question)
    if not chunks or chunks[0]["distance"] > REFUSAL_DISTANCE:
        return {"question": question, "chunks": chunks, "prompt": None,
                "answer": REFUSAL, "refused_by": "distance gate (code)"}
    prompt = build_prompt(question, chunks)
    return {"question": question, "chunks": chunks, "prompt": prompt,
            "answer": llm(prompt), "refused_by": None}


# ---------------------------------------------------------------- HTTP face
app = FastAPI(title="Trailmark RAG")


class AskIn(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok", "chunks": collection().count()}


@app.post("/ask")
def ask_endpoint(body: AskIn):
    out = ask(body.question)
    return {"answer": out["answer"],
            "sources": [c["source"] for c in out["chunks"]]}


# ---------------------------------------------------------------- CLI face
def cli_ask(question):
    out = ask(question)
    print(f"QUESTION: {question}\n")
    print(f"RETRIEVED CHUNKS (top {len(out['chunks'])}):")
    for i, c in enumerate(out["chunks"], 1):
        print(f"[{i}] {c['source']} (distance {c['distance']})")
        for ln in c["text"].splitlines():
            print(f"    {ln}")
    if out["prompt"]:
        print("\nPROMPT SENT TO THE MODEL:")
        print(out["prompt"])
    else:
        print(f"\n(no prompt sent — {out['refused_by']})")
    print(f"\nANSWER:\n{out['answer']}")


def cli_compare(question):
    print(f"QUESTION: {question}\n")
    print("KEYWORD SEARCH (shared content words):")
    for i, r in enumerate(keyword_search(question), 1):
        print(f"[{i}] {r['source']} — shared words: "
              f"{', '.join(r['shared']) if r['shared'] else 'NONE'}")
    print("\nEMBEDDING SEARCH (nearest by meaning):")
    for i, r in enumerate(retrieve(question), 1):
        print(f"[{i}] {r['source']} (distance {r['distance']})")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "ingest":
        chunks = ingest()
        print(f"ingested {len(chunks)} chunks from "
              f"{len(set(c['source'] for c in chunks))} files")
        for c in chunks:
            print(f"  {c['id']}: {c['text'].splitlines()[0][:60]}")
    elif cmd == "ask":
        cli_ask(sys.argv[2])
    elif cmd == "compare":
        cli_compare(sys.argv[2])
    else:
        print(__doc__)
