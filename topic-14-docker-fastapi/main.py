"""Tiny notes API — the demo app we dockerize in Topic #14.

Three endpoints are enough to prove a container works:
  GET  /health  -> {"status": "ok"}        (used by the Docker HEALTHCHECK)
  GET  /notes   -> list of notes
  POST /notes   -> add a note  {"text": "..."}
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Notes API")

notes: list[dict] = [{"id": 1, "text": "Ship it in a container"}]


class NoteIn(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/notes")
def list_notes():
    return notes


@app.post("/notes", status_code=201)
def add_note(note: NoteIn):
    new = {"id": len(notes) + 1, "text": note.text}
    notes.append(new)
    return new
