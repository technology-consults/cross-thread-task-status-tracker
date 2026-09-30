---
id: etf-signal-intraday-offhours
title: ETF intraday signal watch (off-hours)
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  alignment: aligned
  at: 2026-09-29T20:00:00
  catchup: latest
  dom: []
  dow: []
  every: 6h
  kind: interval
  month: []
  time: null
  timezone: America/Toronto
delivery:
- chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: interval@6h
path: /home/hatch/workspace/goals/etf-price-updates/crons/hourly/etf-signal-intraday-offhours__interval@6h.md
is_heartbeat: false
is_system: false
---
Overnight/weekend strong-signal watch for QQQ, SPY, and GLD, delivered to the Trading chat. Chat delivery only — never email. DEFAULT IS SILENCE: only send when a genuinely strong new signal fires. Signals are rule-based and informational only, not financial advice.

Gate checks first — get the current local date and time in America/Toronto. Read ~/workspace/shared/holidays/nyse_holidays.json (if the file is missing or unreadable, fetch holidays/nyse_holidays.json from the technology-consults/cross-thread-task-status-tracker repo (@ main) via the GitHub API, save it to ~/workspace/shared/holidays/nyse_holidays.json, and use that copy going forward — never rebuild the list from a web search; if the repo copy is unreachable too, do not guess and end the run with one brief failure note). Decide whether this firing should run:
- If today is Saturday or Sunday, or today's date (YYYY-MM-DD) is in the file's "holidays" list: proceed ONLY if the local time is between 20:00 and 20:59 (the once-a-day weekend/holiday check). Otherwise stay silent.
- If today is a Monday–Friday trading day: proceed ONLY if the local time is outside 04:00–20:00 (the market-hours job covers 04:00–20:00). Otherwise stay silent.
If the gate says stay silent: no message, no state change, end.

Phase 1 — cheap check (quotes + headlines only):
1. Fetch current quotes for QQQ, SPY, GLD: finance vertical for QQQ (verify symbol exactly QQQ); stockanalysis.com/etf/<ticker>/history/ for SPY/GLD (shows live/after-hours values). Note the session: "Market closed" (overnight/weekend — prices may be stale or futures-driven).
2. Run 2–3 browser_search news queries: stock market news right now (S&P 500 / Nasdaq / VIX, futures); gold price news right now (geopolitics/war, safe-haven demand, dollar, yields); any Fed/economic headlines right now.
3. Read ~/workspace/goals/etf-price-updates/hidden_files/etf_signal_state.json for the last published signal per symbol.
Trigger Phase 2 ONLY if: any symbol moved ≥1.5% since its last published signal price, OR a major market-moving headline appeared (rate shock, CPI surprise, major war/geopolitical escalation, emergency Fed action). Otherwise stay silent and end.

Phase 2 — full analysis (only when triggered):
1. Fetch ~6 months of daily closes per symbol via Nasdaq historical tables (6M range), dropping SPY phantom holiday rows (diff vs QQQ/GLD dates). Never invent data.
2. Gather the full macro factor set (same 5 searches as the morning job: Fed/FOMC, CPI + upcoming dates from ~/workspace/repos/trading/src/econ_events.json, jobs, market trend/VIX, gold: war/geopolitics + safe-haven + dollar + yields + central-bank buying). Flag major=true only for genuinely market-moving events.
3. Write /tmp/etf_signal_input.json (same shape as the morning job, session "Market closed") and run: python3 ~/workspace/repos/trading/src/build_signals.py /tmp/etf_signal_input.json /tmp/etf_signal_out.json --mode intraday --state ~/workspace/goals/etf-price-updates/hidden_files/etf_signal_state.json
4. If the output's "send" is true: your final chat message is EXACTLY the "message" string from the output JSON, verbatim — then re-run the script with --update-state appended to record the published signals. If "send" is false: stay silent, no message, no state change.
