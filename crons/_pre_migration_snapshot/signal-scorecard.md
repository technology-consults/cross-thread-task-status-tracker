---
id: signal-scorecard
title: Signal scorecard
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  alignment: aligned
  at: null
  catchup: latest
  dom: []
  dow: []
  every: null
  kind: daily
  month: []
  time: 08:42:00
  timezone: America/Toronto
delivery:
- chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: 300
schedule_key: daily@08:42:00
path: /home/hatch/workspace/goals/etf-price-updates/crons/daily/signal-scorecard__daily@08:42:00.md
is_heartbeat: false
is_system: false
---
Daily published-signal scorecard for QQQ, SPY, and GLD, delivered to the Trading chat. Chat delivery only — never email. Rule-based and informational only, not financial advice — the card footer says so; never present scores as advice or guarantees.

First, decide whether this run should do anything. Get the current local date and time in America/Toronto. Only proceed if ALL of these hold:
1. Today is Monday–Friday.
2. Today is a NYSE trading day — read ~/workspace/shared/holidays/nyse_holidays.json; if today's date (YYYY-MM-DD) is in the "holidays" list, today is a holiday. If the file is missing or unreadable, fetch holidays/nyse_holidays.json from the technology-consults/cross-thread-task-status-tracker repo (@ main) via the GitHub API, save it to ~/workspace/shared/holidays/nyse_holidays.json, and use that copy going forward. Never rebuild the list from a web search; if the repo copy is unreachable too, do not guess — end the run with one brief failure note.
If any check fails, stay silent and end the run with no user-facing message.

Otherwise:
1. Run: python3 ~/workspace/repos/trading/src/build_scorecard.py > /tmp/scorecard.json
2. Read /tmp/scorecard.json — it contains {"post": true/false, "text": "..."}.
3. If post is true: your final chat message is EXACTLY the "text" string — post it verbatim, no added text. Then run: python3 ~/workspace/repos/trading/src/build_scorecard.py --mark-posted
4. If post is false: stay silent and end the run with no user-facing message.

The ledger lives at ~/workspace/goals/etf-price-updates/hidden_files/signal_scorecard.json — the script maintains it; never edit it by hand. Score only signals the engine actually published; never invent or backfill signals, and never recompute the engine's targets.
