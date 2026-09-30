---
id: premarket-heads-up
title: Pre-market heads-up (futures, VIX, dollar, yields)
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
  time: 09:05:00
  timezone: America/Toronto
delivery:
- chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: daily@09:05:00
path: /home/hatch/workspace/goals/etf-price-updates/crons/daily/premarket-heads-up__daily@09:05:00.md
is_heartbeat: false
is_system: false
---
Pre-market heads-up note for the Trading chat: overnight S&P 500 and Nasdaq 100 futures direction, the VIX, the US dollar index, and the 10-year Treasury yield — each in one plain line with its implication for the day. Chat delivery only, never email. Strictly read-only: never create, change, restate, or suppress any published BUY, SELL, or HOLD signal, and never read or write the signal state or ledger.

Run: python3 ~/workspace/goals/etf-price-updates/hidden_files/premarket_note.py

The script prints one line. Handle it as follows:
- If it prints "SKIP: ..." (weekend or NYSE holiday), stay silent and end the run with no user-facing message.
- If it prints "NOTE|<text>", your final chat message is EXACTLY <text> — post it verbatim, no added words, no signal content, no prices repeated outside it.

Data source: public Yahoo Finance chart data, fetched live by the script. The script remembers yesterday's gauge values in ~/workspace/goals/etf-price-updates/hidden_files/premarket_state.json so each note says what changed overnight, and it tracks consecutive data failures (after three failed mornings it says the source needs attention, once). Do not edit or move these files; only the script writes them. If the script itself errors, do not invent readings — end with one brief failure line.
