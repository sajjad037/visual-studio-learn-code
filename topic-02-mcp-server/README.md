# Topic #2 — MCP Servers Explained: Give Your AI Agent Real Tools

Companion code for the Visual Studio Learn tutorial **"MCP Servers Explained: Give Your AI Agent Real Tools"** (publishes Thu Oct 22, 2026 — post and video links are added here at publish time).

## What this is

A working **Model Context Protocol (MCP) server** in Python, plus a small client that calls it — no model, no API key, nothing to buy.

- `server.py` — an MCP server named `project-notes` offering two read-only tools over a tiny SQLite notes database it creates and seeds itself on first run:
  1. **search_notes** — finds notes whose title or body contains a keyword.
  2. **recent_notes** — lists the most recently added notes.
- `client.py` — starts the server as a subprocess over **stdio**, performs the MCP handshake, lists the tools, and calls both — the same sequence a full AI host (a coding assistant, a chat app with tool support) performs, with no model in between.

The type hints in `server.py` become each tool's JSON input schema automatically, and each docstring is the description a model would read — that is the whole contract, no schema is written by hand.

## Prerequisites

- **Python 3.10 or newer** (the tutorial uses 3.12; check with `python --version`). On Windows, if the Microsoft Store opens instead, install Python from python.org and tick "Add python.exe to PATH".
- **No API key, no account.** An MCP server is ordinary local code; testing it involves no model at all. If you later connect it to an AI host, signing in is the host's own setup.

## Environment setup

Create a folder, open a terminal in it, copy `server.py` and `client.py` into it, then create a virtual environment:

```bash
# macOS / Linux
python3 -m venv .venv && source .venv/bin/activate

# Windows PowerShell
py -m venv .venv ; .venv\Scripts\Activate.ps1
```

## Install

From this folder, with the virtual environment active:

```bash
pip install -r requirements.txt
```

That installs the pinned dependency, `mcp[cli]==2.3.0` (MCP Python SDK v2.3.0; the `[cli]` extra adds the `mcp` command used in the Inspect step below). Version note that matters: SDK v2 renamed the class most older tutorials use — code importing `FastMCP` was written for v1 and will not run on v2. This code uses `MCPServer` throughout.

## Build

There is no build step — both files are plain interpreted Python.

## Run

```bash
python client.py
```

Expected output (verified against SDK 2.3.0 on Python 3.12):

```text
Tools: ['search_notes', 'recent_notes']
search_notes -> {"matches": [{"id": 2, "title": "Database backup", "body": "Take a full backup before any schema change and verify the restore.", "tag": "database"}]}
recent_notes -> {"notes": [{"id": 4, "title": "FastAPI startup fix", "tag": "fastapi"}, {"id": 3, "title": "Grafana alert idea", "tag": "monitoring"}]}
```

On the first run the server creates `notes.db` next to `server.py` and seeds it with the four sample notes. Delete `notes.db` any time to reset to the seed data.

**Verify step:** if you see both tool names and both JSON results, the full loop works — subprocess started, handshake completed, tools discovered, calls answered.

## Inspect the server (optional, recommended)

Before or after running the client, look at the server the way a host sees it:

```bash
mcp dev server.py
```

This starts the MCP Inspector, a local web page that connects as a client. Open the address it prints, choose **List Tools**, and you should see both tools with their generated schemas. Call `search_notes` with the keyword `backup`.

Running `python server.py` directly appears to do nothing — that is correct, not a hang: a stdio server waits silently for a client to speak first.

## How to use it

- **Try your own searches:** edit the `arguments` in `client.py` (for example `{"keyword": "deploy"}`), or call the tools from the Inspector.
- **Use your own notes:** edit `SEED_NOTES` in `server.py`, delete `notes.db`, and run again — or point `_connect()` at your own SQLite table with `id / title / body / tag` columns.
- **Connect it to a real AI host:** give the host the same launch information in its configuration (file locations differ per host; use absolute paths, then fully restart the host):

```json
{
  "mcpServers": {
    "project-notes": {
      "command": "C:\\path\\to\\mcp-notes\\.venv\\Scripts\\python.exe",
      "args": ["C:\\path\\to\\mcp-notes\\server.py"]
    }
  }
}
```

- **Safety habits built in — keep them:** both tools are read-only; `limit` is clamped to 1–20; SQL is parameterized, because tool arguments are untrusted input — they may come from a model acting on text someone else wrote.

One more, specific to the Inspector on SDK 2.3.0: `mcp dev` launches your server
through **uv** (the Inspector's server entry is literally a `uv run` command). If
clicking the connect toggle fails with `spawn uv ENOENT`, install uv
(`pip install uv` inside the same virtual environment) and try again.

## Errors you may hit

- **`ModuleNotFoundError: No module named 'mcp.server.fastmcp'`** — you (or a tutorial you followed) are running v1 code on SDK v2. Use `from mcp.server import MCPServer` as here, or pin the old line with `pip install "mcp<2"`. The generations cannot be mixed.
- **The server "hangs" and prints nothing** — it is waiting on stdio for a client; test it with `mcp dev` or `client.py`. Never add a debugging `print()` inside the server: stdout is the JSON-RPC channel, and printing to it corrupts the stream. Log to stderr, or not at all.
- **The host cannot start the server, or finds nothing** — in order: the Python launched is not the venv's Python (use its full path, as in the config above); the `server.py` path is relative or wrong (use absolute paths, then restart the host); or the SDK sits in a different environment. If `mcp dev` works from your venv, the server is innocent and the launch line is at fault.
- **A validation error names the argument you got wrong** — a missing argument returns `Field required`; passing `"five"` where an integer belongs returns `Input should be a valid integer`. Both arrive as tool errors, not crashes, so the caller can retry corrected.

The post's **"Errors you may hit"** section covers these in full (link added at publish time).
