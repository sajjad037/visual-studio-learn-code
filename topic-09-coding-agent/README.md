# Topic 09 — Build Your Own Coding Agent

One Python file. Three tools. One approval gate.

`agent.py` is a complete coding agent built on the Gemini API's manual
function-calling loop. It can read files and run the test suite on its own —
but it can **never write a file until a human approves the exact change** in
the terminal. Every tool is confined to the `demo/` project folder, and the
loop stops after 12 model turns no matter what.

Companion to the Visual Studio Learn tutorial:
- Blog post: https://visualstudiolearn.blogspot.com/2026/11/build-your-own-coding-agent-in-python.html
- Video: https://youtu.be/duquW7F_Ibc

## The demo project

`demo/` is a tiny shopping cart with **one planted bug**: `Cart.add()`
replaces the quantity when the same item is added twice instead of
accumulating it. The suite has 4 tests; exactly 1 fails before the agent
runs:

```
$ cd demo && python -m pytest -q
1 failed, 3 passed
```

The agent's job: run the tests, read the test and the code, find the bug,
propose a fix — wait for your approval — apply it, and prove the suite is
green:

```
4 passed
```

## Run it yourself

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=...   # free key from Google AI Studio — never in code
python agent.py
```

When the agent proposes a write, the run stops and shows you the full new
file content. Type `y` to apply it; anything else denies the write and the
file stays untouched. Try denying the first proposal on purpose — the agent
is told a human refused and must not retry the write.

At the end the agent prints its own bill: the run's real token usage
(input + output, with thinking tokens counted as output, as the rate card
bills them) at $0.75 / $3.75 per 1M tokens (gemini-3.8-flash, Standard tier,
rates verified on Google's pricing page on 2026-11-07, in effect through
Dec 31, 2026).

## The three tools

| Tool | What it does | Guardrail |
|------|--------------|-----------|
| `read_file` | Read a file in the project | Resolved-path confinement to `demo/` |
| `run_tests` | Run the pytest suite, return the output tail | Fixed command, project folder only |
| `write_file` | **Propose** a whole-file write | Human y/n approval gate before anything is saved |

There is deliberately **no shell tool and no network tool**.

## Versions

- Python 3.12
- google-genai 3.0.0 (pinned — the manual loop uses explicit
  `FunctionDeclaration`s; function responses return with role `"tool"`,
  the pattern in the current SDK docs)
- pytest 9.2.0
- Model: `gemini-3.8-flash`
