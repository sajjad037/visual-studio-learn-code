# Versions used in this test

Everything below is what the October 31, 2026 test actually ran —
pinned so the run can be reproduced.

| Item | Version / value |
|---|---|
| TradingAgents | **0.7.1**, installed from the upstream release tag `v0.7.1` |
| Tag commit (HEAD) | `c4544913a14ed3df5f1ed7b9e8483270ce20682a` |
| Upstream repo | https://github.com/TauricResearch/TradingAgents |
| Install route | `pip install .` from the cloned tag (no `requirements.txt` — the framework's own packaging pins its dependencies) |
| Python | **3.12.3** (framework requires 3.11+) |
| LLM provider | Google (Gemini), via an AI Studio API key in the environment |
| Models — attempts 1–3 | deep `gemini-3.8-flash` · quick `gemini-3.5-flash-lite` |
| Models — attempt 5 (completed) | deep `gemini-3.5-flash` · quick `gemini-3.1-flash-lite` |
| Run | NVDA · analysis date 2026-10-09 · analysts market,social,news,fundamentals · 1 debate round · 1 risk round · `--save --no-show` |
| Cost | $0 — Gemini API free tier throughout (caps observed: 20 requests/day for gemini-3.8-flash, 15/day for gemini-3.5-flash-lite, per project per model) |

Repository figures quoted in the post (118,913 stars, 22,731 forks,
884 watchers) were read from the project's GitHub page on
October 31, 2026 — a dated snapshot, not a permanent fact.
