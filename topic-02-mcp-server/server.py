"""A tiny MCP server that searches a local project-notes database."""

import json
import sqlite3
from pathlib import Path

from mcp.server import MCPServer

DB_PATH = Path(__file__).with_name("notes.db")

SEED_NOTES = [
    ("Deploy checklist", "Build the image, run the tests, tag the release, then deploy.", "deploy"),
    ("Database backup", "Take a full backup before any schema change and verify the restore.", "database"),
    ("Grafana alert idea", "Alert when the error rate stays above two percent for ten minutes.", "monitoring"),
    ("FastAPI startup fix", "The startup error came from a missing environment variable, not the code.", "fastapi"),
]


def _connect() -> sqlite3.Connection:
    """Open the notes database, creating and seeding it on first use."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS notes "
        "(id INTEGER PRIMARY KEY, title TEXT, body TEXT, tag TEXT)"
    )
    count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO notes (title, body, tag) VALUES (?, ?, ?)", SEED_NOTES
        )
        conn.commit()
    return conn


mcp = MCPServer("project-notes")


@mcp.tool()
def search_notes(keyword: str, limit: int = 5) -> str:
    """Search project notes for a keyword in the title or body.

    Args:
        keyword: Word or phrase to look for, for example "backup".
        limit: Maximum number of notes to return, between 1 and 20.
    """
    limit = max(1, min(limit, 20))
    like = f"%{keyword}%"
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, title, body, tag FROM notes "
            "WHERE title LIKE ? OR body LIKE ? ORDER BY id LIMIT ?",
            (like, like, limit),
        ).fetchall()
    if not rows:
        return json.dumps({"matches": [], "message": f"No notes match '{keyword}'."})
    return json.dumps(
        {
            "matches": [
                {"id": r[0], "title": r[1], "body": r[2], "tag": r[3]} for r in rows
            ]
        }
    )


@mcp.tool()
def recent_notes(limit: int = 3) -> str:
    """List the most recently added project notes.

    Args:
        limit: How many recent notes to return, between 1 and 20.
    """
    limit = max(1, min(limit, 20))
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, title, tag FROM notes ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return json.dumps(
        {"notes": [{"id": r[0], "title": r[1], "tag": r[2]} for r in rows]}
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
