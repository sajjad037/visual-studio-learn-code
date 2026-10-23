"""Small AI App #1: a PDF Q&A app built with FastAPI and Gemini.

Companion code for the Visual Studio Learn post and video
"Small AI App #1: Build a PDF Q&A App with FastAPI + Gemini".

Upload a PDF, the app extracts and chunks its text, and each question is
answered by Gemini using only the chunks that match the question — with
the token count and estimated cost of every answer reported back.

Requires: Python 3.12, the packages in requirements.txt, and a Gemini
API key in the GEMINI_API_KEY environment variable. See README.md.
"""

import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from io import BytesIO

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from google import genai
from pydantic import BaseModel
from pypdf import PdfReader

logger = logging.getLogger("pdf_qa")
logging.basicConfig(level=logging.INFO)

MODEL = "gemini-3.8-flash"
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB upload limit
CHUNK_SIZE = 1000  # characters per chunk
CHUNK_OVERLAP = 150  # characters shared between neighbouring chunks
TOP_CHUNKS = 4  # chunks sent to the model with each question

# Published pay-as-you-go rates for gemini-3.8-flash, US$ per 1M tokens.
INPUT_RATE_PER_MILLION = 0.75
OUTPUT_RATE_PER_MILLION = 3.75


@dataclass
class StoredDocument:
    """One uploaded PDF: its name, page count, and text chunks."""

    filename: str
    pages: int
    chunks: list[str] = field(default_factory=list)


# In-memory store: doc_id -> document. Deliberately simple — restarting
# the server forgets every upload, which is fine for a learning app and
# is the first thing to replace (with real storage) in a production one.
DOCUMENTS: dict[str, StoredDocument] = {}

app = FastAPI(title="PDF Q&A — Small AI App #1")


def extract_text(pdf_bytes: bytes) -> tuple[str, int]:
    """Extract all text from PDF bytes. Returns (text, page_count).

    Raises ValueError when the file cannot be parsed as a PDF at all.
    A scanned, image-only PDF parses fine but yields almost no text —
    the caller treats that as its own, separate failure.
    """
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
    except Exception as exc:
        raise ValueError(f"Could not read that file as a PDF: {exc}") from exc
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages), len(pages)


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character chunks.

    Overlap exists so a sentence that straddles a chunk boundary still
    appears whole in at least one chunk the model can read.
    """
    cleaned = re.sub(r"\s+", " ", text).strip()
    chunks = []
    start = 0
    while start < len(cleaned):
        chunks.append(cleaned[start : start + size])
        start += size - overlap
    return [c for c in chunks if c.strip()]


STOPWORDS = {
    "the", "and", "for", "are", "was", "what", "when", "where", "which",
    "does", "did", "how", "why", "who", "this", "that", "with", "from",
    "have", "has", "can", "its", "it", "is", "in", "on", "of", "to", "a", "an",
}


def _meaningful_words(text: str) -> set[str]:
    """Lowercase word set with stopwords removed.

    Without this, a question like "What is the…" matches every chunk in
    the document on the words "what" and "the" alone, and the scoring
    below would measure grammar instead of topic.
    """
    return {
        w
        for w in re.findall(r"[a-z0-9]+", text.lower())
        if len(w) > 2 and w not in STOPWORDS
    }


def relevant_chunks(chunks: list[str], question: str, limit: int = TOP_CHUNKS) -> list[str]:
    """Pick the chunks that share the most words with the question.

    This is plain keyword overlap, not semantic search — no embeddings,
    no vector database. It is honest about its limits: it finds chunks
    that use the question's words, and misses paraphrases. That trade is
    the right size for a first app; embeddings are the upgrade path.
    """
    words = _meaningful_words(question)
    if not words:
        return []
    scored = []
    for index, chunk in enumerate(chunks):
        score = len(words & _meaningful_words(chunk))
        if score:
            scored.append((score, index, chunk))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [chunk for _, _, chunk in scored[:limit]]


class AskRequest(BaseModel):
    doc_id: str
    question: str


@app.get("/health")
def health() -> dict:
    """Tiny liveness check: confirms the server is up."""
    return {"status": "ok", "documents_loaded": len(DOCUMENTS)}


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    """Accept one PDF, extract and chunk its text, and store it.

    Returns the document id the client must send with every question,
    plus the page and chunk counts so the reader can see the pipeline
    actually did the work.
    """
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")
    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"That file is over the {MAX_FILE_BYTES // (1024 * 1024)} MB limit.",
        )
    try:
        text, page_count = extract_text(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(
            status_code=422,
            detail=(
                "No readable text was found in that PDF. Scanned or "
                "image-only PDFs need OCR before an app like this can "
                "read them."
            ),
        )
    doc_id = uuid.uuid4().hex[:8]
    DOCUMENTS[doc_id] = StoredDocument(
        filename=file.filename, pages=page_count, chunks=chunks
    )
    logger.info("stored %s: %d pages, %d chunks", file.filename, page_count, len(chunks))
    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "pages": page_count,
        "characters": len(text),
        "chunks": len(chunks),
    }


@app.post("/ask")
def ask(request: AskRequest) -> dict:
    """Answer one question from the stored chunks of one document.

    Only the best-matching chunks are sent to Gemini — never the whole
    document — which is what keeps each question cheap and inside the
    model's context limits. The response carries the real token counts
    the API reported and the cost they work out to.
    """
    document = DOCUMENTS.get(request.doc_id)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Unknown document. Upload a PDF first (uploads are forgotten when the server restarts).",
        )
    chunks = relevant_chunks(document.chunks, request.question)
    if not chunks:
        return {
            "answer": (
                "No passage in this document shares words with that "
                "question, so nothing was sent to the model. Try "
                "rephrasing with words the document itself uses."
            ),
            "chunks_used": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    context = "\n\n---\n\n".join(chunks)
    prompt = (
        "Answer the question using only the document passages below. "
        "If the passages do not contain the answer, say so plainly "
        "instead of guessing.\n\n"
        f"Passages:\n{context}\n\nQuestion: {request.question}"
    )
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set on the server. See the setup steps in the README.",
        )
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=MODEL, contents=prompt)
    except Exception as exc:  # surface API failures as a clean 502, not a stack trace
        logger.exception("Gemini call failed")
        raise HTTPException(status_code=502, detail=f"Gemini API error: {exc}") from exc

    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count or 0
    output_tokens = usage.candidates_token_count or 0
    cost = (
        input_tokens * INPUT_RATE_PER_MILLION
        + output_tokens * OUTPUT_RATE_PER_MILLION
    ) / 1_000_000
    logger.info(
        "ask on %s: %d chunks, %d in / %d out tokens",
        request.doc_id,
        len(chunks),
        input_tokens,
        output_tokens,
    )
    return {
        "answer": response.text,
        "chunks_used": len(chunks),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": round(cost, 6),
    }


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the one-page UI: upload a PDF, then ask it questions."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>PDF Q&amp;A — Small AI App #1</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 16px; }
  h1 { font-size: 24px; }
  .box { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 16px 0; }
  #answer { white-space: pre-wrap; }
  .meta { color: #555; font-size: 14px; }
  button { padding: 8px 16px; cursor: pointer; }
  input[type=text] { width: 75%; padding: 8px; }
</style>
</head>
<body>
<h1>PDF Q&amp;A</h1>
<p>Upload a PDF, then ask it questions. Answers come only from the
document, and every answer shows what it cost.</p>

<div class="box">
  <input type="file" id="pdf" accept="application/pdf">
  <button onclick="uploadPdf()">Upload PDF</button>
  <p class="meta" id="uploadStatus">No document uploaded yet.</p>
</div>

<div class="box">
  <input type="text" id="question" placeholder="Ask a question about the document">
  <button onclick="askQuestion()">Ask</button>
  <p id="answer"></p>
  <p class="meta" id="askMeta"></p>
</div>

<script>
let docId = null;

async function uploadPdf() {
  const fileInput = document.getElementById('pdf');
  const status = document.getElementById('uploadStatus');
  if (!fileInput.files.length) { status.textContent = 'Choose a PDF first.'; return; }
  const form = new FormData();
  form.append('file', fileInput.files[0]);
  status.textContent = 'Uploading and reading…';
  const res = await fetch('/upload', { method: 'POST', body: form });
  const data = await res.json();
  if (!res.ok) { status.textContent = 'Upload failed: ' + data.detail; return; }
  docId = data.doc_id;
  status.textContent = 'Loaded "' + data.filename + '": ' + data.pages +
    ' pages, ' + data.characters + ' characters, split into ' +
    data.chunks + ' chunks. You can ask questions now.';
}

async function askQuestion() {
  const answer = document.getElementById('answer');
  const meta = document.getElementById('askMeta');
  if (!docId) { answer.textContent = 'Upload a PDF first.'; return; }
  const question = document.getElementById('question').value;
  answer.textContent = 'Thinking…';
  const res = await fetch('/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ doc_id: docId, question: question })
  });
  const data = await res.json();
  if (!res.ok) { answer.textContent = 'Error: ' + data.detail; meta.textContent = ''; return; }
  answer.textContent = data.answer;
  meta.textContent = 'Used ' + data.chunks_used + ' chunks · ' +
    data.input_tokens + ' input tokens · ' + data.output_tokens +
    ' output tokens · about $' + data.estimated_cost_usd.toFixed(6);
}
</script>
</body>
</html>"""
