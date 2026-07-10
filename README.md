# citewise

An in-house, open-source replacement for **Perplexity Pro** ($20/mo "AI answer engine").

## Why this exists
Perplexity Pro costs $20/month and gates the good stuff: the Free tier caps you at
**5 pro searches** and **3 deep-research runs/day**, and the whole thing is
**vendor-locked** — your notes, history, and queries live on their servers. We
built our own version from scratch. No paid API, no account, no query caps.

## How it's enhanced (vs Perplexity Free/Pro)
- **Unlimited searches** — no 5-query wall, no 500/day ceiling.
- **Self-hosted** — runs on your machine, your queries stay yours.
- **Zero paid dependencies** — search is DuckDuckGo (no key); synthesis is any
  OpenAI-compatible endpoint you point it at (or off, for extractive mode).
- **Deep-research loop** (`--deep`) — spawns follow-up sub-queries and merges,
  something the Free tier can't do at all.
- **Drops into your vault** — `--save` writes a cited markdown report you can
  drop straight into Obsidian.
- **Maintenance heartbeat** (`--self-check`) — the "updates for life" promise:
  a cron can verify the pipeline still works and alert you if DuckDuckGo changes.

## Install
```bash
git clone https://github.com/Mellowambience/our-own-citewise.git
cd our-own-citewise
python3 citewise.py "your question" --save report.md
```
No `pip install` required — standard library only.

## Usage
```bash
# quick cited brief (extractive, no API key needed)
python3 citewise.py "latest open-source local LLM inference advances 2026"

# deep-research loop with follow-up queries
python3 citewise.py "best self-hosted AI search engines" --deep

# full LLM synthesis (optional) — set your endpoint
export OPENAI_BASE_URL="https://your-endpoint/v1"
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="your-model"
python3 citewise.py "compare RAG vs long-context" --deep --save out.md

# verify the pipeline still works (cron this)
python3 citewise.py --self-check
```

## Use it free
MIT licensed. Clone, fork, self-host. No account needed.

## Support (voluntary tips)
If it helps you, tip jar: **Cash App $MarsEatPlanet**
Tips are never required and never gate features.

#our-own #open-source #perplexity-alternative
