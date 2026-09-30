---
id: premarket-heads-up
title: Pre-market heads-up (futures, VIX, dollar, yields)
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 09:42:00
delivery:
  - chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Pre-market heads-up note for the Trading chat: overnight S&P 500 and Nasdaq 100 futures direction, the VIX, the US dollar index, and the 10-year Treasury yield — each in one plain line with its implication for the day. Chat delivery only, never email. Strictly read-only: never create, change, restate, or suppress any published BUY, SELL, or HOLD signal, and never read or write the signal state or ledger.

Run: python3 ~/workspace/goals/etf-price-updates/hidden_files/premarket_note.py

The script prints one line. Handle it as follows:
- If it prints "SKIP: ..." (weekend or NYSE holiday), stay silent and end the run with no user-facing message.
- If it prints "NOTE|<text>", your final chat message is EXACTLY <text> — post it verbatim, no added words, no signal content, no prices repeated outside it.

Data source: public Yahoo Finance chart data, fetched live by the script. The script remembers yesterday's gauge values in ~/workspace/goals/etf-price-updates/hidden_files/premarket_state.json so each note says what changed overnight, and it tracks consecutive data failures (after three failed mornings it says the source needs attention, once). Do not edit or move these files; only the script writes them. If the script itself errors, do not invent readings — end with one brief failure line.
