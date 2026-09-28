---
id: signal-scorecard
title: Signal scorecard
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 08:42:00
timeout_secs: 300
delivery:
  - chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Daily published-signal scorecard for QQQ, SPY, and GLD, delivered to the Trading chat. Chat delivery only — never email. Rule-based and informational only, not financial advice — the card footer says so; never present scores as advice or guarantees.

First, decide whether this run should do anything. Get the current local date and time in America/Toronto. Only proceed if ALL of these hold:
1. Today is Monday–Friday.
2. Today is a NYSE trading day (not a US stock market holiday — if unsure, do a quick web search for the NYSE holiday calendar for the current year).
If any check fails, stay silent and end the run with no user-facing message.

Otherwise:
1. Run: python3 ~/workspace/repos/trading/src/build_scorecard.py > /tmp/scorecard.json
2. Read /tmp/scorecard.json — it contains {"post": true/false, "text": "..."}.
3. If post is true: your final chat message is EXACTLY the "text" string — post it verbatim, no added text. Then run: python3 ~/workspace/repos/trading/src/build_scorecard.py --mark-posted
4. If post is false: stay silent and end the run with no user-facing message.

The ledger lives at ~/workspace/goals/etf-price-updates/hidden_files/signal_scorecard.json — the script maintains it; never edit it by hand. Score only signals the engine actually published; never invent or backfill signals, and never recompute the engine's targets.
