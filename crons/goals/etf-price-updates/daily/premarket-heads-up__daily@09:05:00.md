---
id: premarket-heads-up
title: Pre-market heads-up (futures, VIX, dollar, yields, oil, Nasdaq Composite, silver)
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 09:05:00
delivery:
  - chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
metadata:
  originating_chat_context_json: '{"chat_id":"3c672068-efb2-446c-9e50-aa0a3d02adf1","origin_provider":"main","chat_kind":"direct","provider":"main","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Pre-market heads-up note for the Trading chat: overnight S&P 500 and Nasdaq 100 futures direction, the VIX, the US dollar index, the 10-year Treasury yield, WTI crude oil, the Nasdaq Composite, and silver — each in one plain line with its implication for the day. Published as a time-stamped PDF (one bullet per gauge; the label before the colon in each bullet is bold in its own distinct color, the rest normal text). Chat delivery only, never email. Strictly read-only: never create, change, restate, or suppress any published BUY, SELL, or HOLD signal, and never read or write the signal state or ledger.

Run: python3 ~/workspace/goals/etf-price-updates/hidden_files/premarket_note.py

The script prints one line. Handle it as follows:
- If it prints "SKIP: ..." (weekend or NYSE holiday), stay silent and end the run with no user-facing message.
- If it prints "NOTE|<text>", save <text> to /tmp/premarket_note.txt, then run:
  python3 ~/workspace/repos/trading/src/build_premarket_pdf.py /tmp/premarket_note.txt ~/workspace/goals/etf-price-updates/files/premarket-<YYYY-MM-DD>-<HHMM>-ET.pdf
  (time-stamped from the run time in America/Toronto, e.g. premarket-2026-10-02-0905-ET.pdf).
  Your final chat message is the one-line header "Pre-market heads-up · <Day Mon DD> · <~h:MM AM/PM ET>" (date from the note's first line, time from the run clock) plus the PDF attached as an own-line sandbox link — no note text repeated outside the PDF, no signal content.

Data source: public Yahoo Finance chart data, fetched live by the script. The script remembers yesterday's gauge values in ~/workspace/goals/etf-price-updates/hidden_files/premarket_state.json so each note says what changed overnight, and it tracks consecutive data failures (after three failed mornings it says the source needs attention, once). Do not edit or move these files; only the script writes them. If the script itself errors, do not invent readings — end with one brief failure line.
