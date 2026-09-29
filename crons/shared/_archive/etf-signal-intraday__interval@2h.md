---
id: etf-signal-intraday
title: ETF intraday signal watch
enabled: false
owner: goal:etf-price-updates
mode: task
schedule:
  kind: interval
  timezone: America/Toronto
  at: 2026-09-25T09:30:00
  every: 2h
delivery:
  - chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
metadata:
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Intraday strong-signal watch for QQQ, SPY, and GLD, delivered to the Trading chat. Chat delivery only — never email. DEFAULT IS SILENCE: only send when a genuinely strong new signal fires. Signals are rule-based and informational only, not financial advice.

Gate checks first — get the current local date and time in America/Toronto. Proceed ONLY if ALL hold:
1. Monday–Friday.
2. NYSE trading day (if unsure, quick web search of the NYSE holiday calendar).
3. Local time between 09:30 and 20:00.
Otherwise stay silent, no message, no state change.

Phase 1 — cheap check (quotes + headlines only):
1. Fetch current quotes for QQQ, SPY, GLD: finance vertical for QQQ (verify symbol exactly QQQ); stockanalysis.com/etf/<ticker>/history/ for SPY/GLD (shows live/after-hours values). Note the session: "Market open" (09:30–16:00), "After hours" (16:00–20:00).
2. Run 2–3 browser_search news queries: stock market news right now (S&P 500 / Nasdaq / VIX); gold price news right now (geopolitics/war, safe-haven demand, dollar, yields); any Fed/economic headlines right now.
3. Read ~/workspace/goals/etf-price-updates/hidden_files/etf_signal_state.json for the last published signal per symbol.
Trigger Phase 2 ONLY if: any symbol moved ≥1.5% since its last published signal price, OR a major market-moving headline appeared (rate shock, CPI surprise, major war/geopolitical escalation, emergency Fed action). Otherwise stay silent and end.

Phase 2 — full analysis (only when triggered):
1. Fetch ~6 months of daily closes per symbol via Nasdaq historical tables (6M range), dropping SPY phantom holiday rows (diff vs QQQ/GLD dates). Never invent data.
2. Gather the full macro factor set (same 5 searches as the morning job: Fed/FOMC, CPI + upcoming dates from ~/workspace/repos/trading/src/econ_events.json, jobs, market trend/VIX, gold: war/geopolitics + safe-haven + dollar + yields + central-bank buying). Flag major=true only for genuinely market-moving events.
3. Write /tmp/etf_signal_input.json (same shape as the morning job, session "Market open" or "After hours") and run: python3 ~/workspace/repos/trading/src/build_signals.py /tmp/etf_signal_input.json /tmp/etf_signal_out.json --mode intraday --state ~/workspace/goals/etf-price-updates/hidden_files/etf_signal_state.json
4. If the output's "send" is true: your final chat message is EXACTLY the "message" string from the output JSON, verbatim — then re-run the script with --update-state appended to record the published signals. If "send" is false: stay silent, no message, no state change.
