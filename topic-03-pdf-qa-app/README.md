# Small AI App #1 — PDF Q&A with FastAPI + Gemini

Companion code for the Visual Studio Learn post and video
**"Small AI App #1: Build a PDF Q&A App with FastAPI + Gemini (Upload a PDF, Ask It Questions)"**.

Upload a PDF in the browser, and the app extracts its text, splits it into
chunks, and answers your questions with Google Gemini using only the chunks
that match each question. Every answer reports the tokens it used and what
they cost. One file, no framework beyond FastAPI, no vector database.

## What it does

- `POST /upload` — accepts one PDF (max 10 MB), extracts its text with
  pypdf, splits it into 1,000-character chunks with 150 characters of
  overlap, and stores them in memory under a short document id.
- `POST /ask` — scores the chunks against your question by keyword
  overlap (stopwords removed), sends the best four to Gemini with an
  instruction to answer only from those passages, and returns the answer
  plus the real input/output token counts and the estimated cost.
- `GET /` — a one-page web UI for uploading and asking.
- `GET /health` — liveness check.
- If no chunk shares a meaningful word with the question, the app answers
  without calling the model at all — zero tokens, zero cost.

## Prerequisites

- Python 3.10 or newer (the tutorial uses **Python 3.12.3**).
- A **Gemini API key** (free tier is enough — see below).
- Any text-based PDF to test with. Scanned/image-only PDFs have no text
  layer and are rejected with an explanation (they need OCR first).

## Environment setup

### 1. Get a Gemini API key (free, no card)

1. Go to **aistudio.google.com** and sign in with a Google account.
2. Click **Get API key** (left sidebar, key icon).
3. Click **Create API key**, choose or create a Google Cloud project when
   asked, and click **Create**.
4. Copy the key that appears. It is shown in your key list whenever you
   need it again.
5. Treat it like a password: never paste it into code, a screenshot, or a
   public repository. This app reads it from an environment variable only.

No billing or credit card is required for the free tier. The free tier has
daily request limits; the pay-as-you-go rates used for the app's cost
readout are US$0.75 per million input tokens and US$3.75 per million
output tokens for `gemini-3.8-flash`.

### 2. Create the project environment

```bash
mkdir pdf-qa && cd pdf-qa
python3 -m venv .venv && source .venv/bin/activate   # macOS / Linux
# Windows PowerShell:  py -m venv .venv ; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Pinned versions (matching the post): FastAPI 0.161.1 · uvicorn 0.54.0 ·
pypdf 6.21.2 · google-genai 2.33.0 · python-multipart 0.0.32.

### 3. Set the key and verify

```bash
export GEMINI_API_KEY="paste-your-key-here"          # macOS / Linux
# Windows PowerShell:  $env:GEMINI_API_KEY = "paste-your-key-here"
```

## Run

```bash
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000** in your browser. Check
**http://127.0.0.1:8000/health** — it should return `{"status": "ok", ...}`.

## Use it

1. Choose a PDF and click **Upload PDF**. The status line reports the
   page count, character count, and chunk count the server extracted.
2. Type a question that uses words from the document and click **Ask**.
3. Read the answer, then the line under it: chunks used, input tokens,
   output tokens, and the estimated cost of that one answer.

API-only use:

```bash
curl -F "file=@handbook.pdf" http://127.0.0.1:8000/upload
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" \
  -d '{"doc_id": "PASTE_DOC_ID", "question": "When is the lottery draw?"}'
```

## Errors you may hit

- **422 on upload** — the PDF has no readable text (scanned/image-only).
  Run it through an OCR tool first.
- **413 on upload** — the file is over the 10 MB limit.
- **404 on ask** — unknown document id; uploads live in memory and are
  forgotten when the server restarts. Upload again.
- **500 on ask** — `GEMINI_API_KEY` is not set in the server's
  environment. Set it and restart the server.
- **502 on ask** — the Gemini API rejected or failed the call (invalid
  key, quota, or a network problem); the message includes the API's own
  error text.

## Deliberate limits (and the upgrade path)

Storage is in-memory, retrieval is keyword overlap rather than embeddings,
and there is no login. Those are tutorial-sized choices, stated openly:
persistent storage, an embeddings index, and authentication are the three
upgrades a production version needs first.

Code samples are provided for learning purposes — test them in your own
environment before using them in anything that matters.
