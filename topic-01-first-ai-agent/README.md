# Topic #1 — Build Your First AI Agent in Python

Companion code for the Visual Studio Learn tutorial **"Build Your First AI Agent in Python (Tool-Calling, Step by Step)"**:

- 📖 Post: https://visualstudiolearn.blogspot.com/2026/10/build-your-first-ai-agent-in-python.html
- 🎬 Video: https://www.youtube.com/watch?v=r0nY3zq9YfE

## What this is

A small command-line AI agent in a single Python file (`first_agent.py`) — no framework, no LangChain. It has two tools:

1. **Weather lookup** — current temperature and wind for any city, from the free Open-Meteo service (no API key needed for weather).
2. **Calculator** — evaluates arithmetic safely by parsing the expression tree. It never uses Python's `eval()`.

You ask one question; the agent decides which tools to call, runs them, reads the results, and answers. Ask it the built-in question — *"Is it warmer in Ottawa or Toronto right now, and what is the temperature difference times two?"* — and it calls the weather tool twice, the calculator once, then answers in plain language.

## Prerequisites

- **Python 3.12** installed (check with `python --version`). The code should also run on 3.10+, but 3.12 is the version the tutorial uses.
- **A free Gemini API key** (setup below — about 2 minutes, no credit card required).
- An internet connection (the agent calls the Gemini API and Open-Meteo).

## Environment setup

### 1. Get your free Gemini API key

1. Open [Google AI Studio](https://aistudio.google.com) and sign in with your Google account. Accept the terms if it is your first visit.
2. Click **Get API key**.
3. Click **Create API key**, then choose **Create API key in new project** — the simplest option for a first key.
4. Google generates the key and shows it to you. Click **Copy**. A Gemini key starts with `AIza`.
5. Treat the key like a password: never post it publicly, never commit it to GitHub. If it ever leaks, delete it on the same page and create a fresh one.

### 2. Set the key as an environment variable

The code reads the key from the `GEMINI_API_KEY` environment variable — it is never written into the source.

```bash
# macOS / Linux
export GEMINI_API_KEY="your-key-here"

# Windows PowerShell
$env:GEMINI_API_KEY="your-key-here"
```

Set it in the same terminal session you will run the script from.

## Install

From this folder:

```bash
pip install -r requirements.txt
```

That installs the single dependency, `google-genai==1.35.0`.

## Build

There is no build step — it is one interpreted Python file.

## Run

```bash
python first_agent.py
```

You should see the agent's tool calls printed as they happen (temperatures will differ every run — that is the live weather):

```text
  step 1: get_weather({'city': 'Ottawa'}) -> {'city': 'Ottawa', 'temperature_c': 9.4, ...}
  step 1: get_weather({'city': 'Toronto'}) -> {'city': 'Toronto', 'temperature_c': 12.1, ...}
  step 2: calculate({'expression': '(12.1 - 9.4) * 2'}) -> {'result': 5.4}

Answer: Toronto is warmer right now, at 12.1°C compared with 9.4°C in Ottawa — a difference of 2.7 degrees, which doubled is 5.4.
```

## How to use it

- **Ask your own question:** edit the question in the `if __name__ == "__main__":` block at the bottom of `first_agent.py`, or import `run_agent("your question")` from your own script.
- **Add your own tool:** write a function with typed arguments and a clear docstring (the model reads the docstring to decide when the tool applies), then add it to the `TOOLS` dictionary.
- **Safety habits built in — keep them:** tools return `{"error": ...}` instead of raising, so one bad call does not kill the run; `MAX_STEPS = 6` caps the loop so the agent always stops; tool arguments are treated as untrusted input.

## Cost

One run of the built-in question makes 3–4 model calls (roughly 1,000–1,500 input tokens, 150–250 output tokens) — well under a tenth of a cent at `gemini-2.5-flash` paid rates, and on the free tier it counts against your daily quota instead.

## Errors you may hit

The post's **"Errors you may hit"** section covers the common ones — `KeyError: 'GEMINI_API_KEY'`, invented tool names, malformed arguments, 429 rate limits, and transient 503s — with the fix for each: https://visualstudiolearn.blogspot.com/2026/10/build-your-first-ai-agent-in-python.html
