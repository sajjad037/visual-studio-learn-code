#!/usr/bin/env bash
# run-test.sh — the exact sequence used for the Visual Studio Learn
# "Open-Source Agent, Tested #1" run of TradingAgents v0.7.1
# (NVDA, analysis date 2026-10-09, tested October 31, 2026).
#
# Prerequisite: a clone of the upstream project with the venv active —
#   git clone https://github.com/TauricResearch/TradingAgents.git
#   cd TradingAgents && git checkout v0.7.1
#   python3 -m venv .venv && source .venv/bin/activate
#   pip install .
# Run this script from inside that clone, with the venv active.

set -euo pipefail

# NOTE (learned the hard way, attempt 1): if your shell carries proxy
# environment variables whose NO_PROXY value contains a bracketed IPv6
# address (e.g. [::1]) — common on corporate and sandboxed machines —
# httpx can fail to parse it as a host:port pair and the run dies
# instantly with "httpx.InvalidURL: Invalid port: ':1]'". Clearing
# NO_PROXY/no_proxy for the run avoids it. This is an environment
# quirk of the machine, not a TradingAgents bug.
unset NO_PROXY no_proxy

# --- Provider key ---------------------------------------------------
# Get a free Gemini API key at aistudio.google.com. Paste YOUR key —
# never commit a real key to a repository.
export GOOGLE_API_KEY=PASTE_YOUR_KEY

# --- Framework configuration (environment overrides) ----------------
export TRADINGAGENTS_LLM_PROVIDER=google
# The model pair that COMPLETED the test (attempt 5): two free-tier
# buckets the earlier attempts had not touched.
export TRADINGAGENTS_DEEP_THINK_LLM=gemini-3.5-flash
export TRADINGAGENTS_QUICK_THINK_LLM=gemini-3.1-flash-lite
# The first pair we ran (attempts 1-3) — kept here for the record; its
# free-tier daily caps (20/day deep, 15/day quick) ran out mid-test:
# export TRADINGAGENTS_DEEP_THINK_LLM=gemini-3.8-flash
# export TRADINGAGENTS_QUICK_THINK_LLM=gemini-3.5-flash-lite
export TRADINGAGENTS_OUTPUT_LANGUAGE=English
export TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
export TRADINGAGENTS_MAX_RISK_ROUNDS=1
export TRADINGAGENTS_CHECKPOINT_ENABLED=true

# --- The run ---------------------------------------------------------
# Past analysis date on purpose: only information available up to
# 2026-10-09 could be used, so the decision can be graded against what
# the price actually did afterwards. --save writes the full report
# bundle; --no-show runs unattended.
#
# --checkpoint lets an interrupted run save its place. Honest note from
# the test: attempt 4's checkpoint resume restarted from the beginning
# instead of resuming, and re-spent quota from zero — the completed
# attempt 5 was a fresh run. Keep the flag, but budget quota as if a
# resume may not rescue you.
tradingagents --ticker NVDA --date 2026-10-09 --analysts market,social,news,fundamentals --save --no-show --checkpoint
