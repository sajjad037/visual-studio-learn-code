# TradingAgents, Tested — Run Configuration & Notes

Companion folder for the Visual Studio Learn post and video
**"Does the 118K-Star AI Trading Agent Actually Work? I Installed and
Tested TradingAgents v0.7.1 — Open-Source Agent, Tested #1"**
(the pilot episode of the *Open-Source Agent, Tested* series).

- **Blog post:** [link added at publish — Visual Studio Learn](https://visualstudiolearn.blogspot.com)
- **The project under test** (credit: Tauric Research): https://github.com/TauricResearch/TradingAgents — star it there, not here, if the test convinces you.

There is no original code of ours in this folder, because that is the
point of the series: the software under test is someone else's project,
installed exactly as its own documentation describes. What this folder
holds is the **exact setup, environment configuration, and run command
used in our test**, plus a short record of what happened — so you can
reproduce the run yourself, on your own machine and your own key.

## What TradingAgents is

A free, open-source (Apache-2.0) Python framework that splits stock
analysis across a team of LLM agents modelled on a trading firm: four
analysts (market/technical, sentiment, news, fundamentals) research in
parallel, two researchers debate the evidence bull-versus-bear, a
trader proposes a decision, and a risk debate plus a portfolio manager
approve or reject it. Approved orders go to a **simulated** exchange.

## Prerequisites

- Python **3.11 or later** (this test used **Python 3.12.3**).
- A language-model provider. This test used the **Google (Gemini)**
  provider with a free AI Studio API key; the framework also supports
  other API providers, a ChatGPT Plus/Pro sign-in
  (`tradingagents login chatgpt`), and local models via Ollama.

## Setup (exactly as run in the test)

```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
git checkout v0.7.1        # the release tag tested — commit c4544913a14ed3df5f1ed7b9e8483270ce20682a

python3 -m venv .venv && source .venv/bin/activate   # macOS / Linux
# Windows PowerShell:  py -m venv .venv ; .venv\Scripts\Activate.ps1

pip install .
```

On the test machine that install finished cleanly, with no errors, and
`tradingagents --help` runs before any API key exists. TradingAgents
is installed from its own repository tag — there is deliberately no
`requirements.txt` in this folder; see `VERSIONS.md` for the pins.

## Configure the Google provider

Get a free Gemini API key at **aistudio.google.com** (Get API key →
Create API key). Treat it like a password: this setup reads it from an
environment variable only — never paste a real key into code, a
screenshot, or a public repository.

Copy `.env.example` from this folder and fill in your key, or export
the variables in your shell:

```bash
export GOOGLE_API_KEY=PASTE_YOUR_KEY
export TRADINGAGENTS_LLM_PROVIDER=google
export TRADINGAGENTS_DEEP_THINK_LLM=gemini-3.5-flash
export TRADINGAGENTS_QUICK_THINK_LLM=gemini-3.1-flash-lite
export TRADINGAGENTS_OUTPUT_LANGUAGE=English
export TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
export TRADINGAGENTS_MAX_RISK_ROUNDS=1
```

`run-test.sh` in this folder runs the whole sequence end to end.

## The run command used

```bash
tradingagents --ticker NVDA --date 2026-10-09 --analysts market,social,news,fundamentals --save --no-show
```

A **past** analysis date (Friday, October 9, 2026) was chosen on
purpose: the framework could only use information available up to that
day, so its decision can be compared against what the price actually
did afterwards. `--save` writes the full report bundle to disk;
`--no-show` runs it unattended.

## What happened in our test (October 31, 2026)

Getting one complete run took **five attempts in 24 minutes**. None of
the four failures was a TradingAgents code bug:

1. **Attempt 1 (7 seconds)** — died instantly on this machine's proxy
   environment: a bracketed IPv6 entry in `NO_PROXY` crashed httpx's
   URL parser (`InvalidURL: Invalid port: ':1]'`). An environment
   issue, fixed by clearing `NO_PROXY`/`no_proxy` for the run.
2. **Attempt 2 (10 minutes)** — analysts and the full bull/bear debate
   completed; the run then died at the Research Manager when the
   Gemini connection dropped mid-request, and the framework's one
   automatic free-text retry hit the same wall.
3. **Attempt 3 (9 minutes 41 seconds)** — same shape, harder wall:
   the Gemini **free tier allows 20 generate-content requests per day,
   per project, per model** for `gemini-3.8-flash`, and attempts 2–3
   had spent the day's allowance (the API suggested retrying in
   ~14.6 hours).
4. **Attempt 4 (33 seconds)** — a `--checkpoint` resume did not resume
   in practice; the run restarted from zero and died at the Market
   Analyst on the *other* model's quota: **15 requests/day** for
   `gemini-3.5-flash-lite`. Two lessons: the free tier meters each
   model separately (which is what made attempt 5 possible), and the
   checkpoint resume did not deliver what it promises in this session.
5. **Attempt 5 (107 seconds, exit 0)** — a fresh run on two untouched
   free-tier buckets, deep = **gemini-3.5-flash** and quick =
   **gemini-3.1-flash-lite**, walked the entire pipeline — analysts,
   debate, research manager, trader, risk debate, portfolio decision —
   and saved the complete report.

**The decision:** Overweight on NVDA — enter $226.73 down to $221.94,
position 1.0x–1.25x, stop-loss $215–$218, horizon 3–6 months.

**What the price did next:** the entry triggered within one trading
day (Oct 12 close $226.32), the price fell through the bottom of the
entry zone on Oct 14, and on **Oct 15 it closed at $217.23 — inside
the decision's own stop-loss band**, so a rules-following holder exits
there at roughly −4% to −6%. By **Oct 30 the close was $204.64,
−10.7%** from the analysis-date close of $229.28. The directional call
was wrong; the stop-loss roughly halved the damage. One run, one
ticker, one date — a test result, not a track record.

**Measured cost: $0.** Every attempt ran on the Gemini free tier. The
real currency was quota and 24 minutes of wall clock, of which the
successful pipeline itself took 107 seconds.

## Errors you may hit

- **`GOOGLE_API_KEY is not set; there is no terminal to ask for it.`**
  — the run stops before doing any work when no key is configured and
  there is no interactive terminal. Export the variable first.
- **429 `RESOURCE_EXHAUSTED` on the free tier** — per-model daily caps
  (20/day and 15/day observed here). Spread runs across models, wait
  for the daily reset, or use a paid tier.
- **Data vendors failing mid-run** — observed: Yahoo Finance news
  timeouts, a Reddit RSS 403, and the optional FRED source skipped
  because no `FRED_API_KEY` was set. The framework fell back and
  carried on each time, and the affected analysts disclosed the gap in
  their reports. Note that sentiment sources do not do history: a
  past-date analysis will have a blind sentiment desk.
- **`--checkpoint` resume** — in this test it restarted from the
  beginning instead of resuming. Budget your quota accordingly.

## Versions

See `VERSIONS.md` for the full pin list (framework tag and commit,
Python version, and both model pairs used).

---

*Research only: TradingAgents is a research framework, and this folder
documents an engineering test of it. Nothing here is financial,
investment, or trading advice.*
