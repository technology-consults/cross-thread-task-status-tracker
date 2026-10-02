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
  originating_chat_context_json: '{"chat_id":"3c672068-efb2-446c-9e50-aa0a3d02adf1","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Daily published-signal scorecard for QQQ, SPY, and GLD, delivered to the Trading chat. Chat delivery only — never email. Rule-based and informational only, not financial advice — the card footer says so; never present scores as advice or guarantees.

First, decide whether this run should do anything. Get the current local date and time in America/Toronto. Only proceed if ALL of these hold:
1. Today is Monday–Friday.
2. Today is a NYSE trading day — read ~/workspace/shared/holidays/nyse_holidays.json; if today's date (YYYY-MM-DD) is in the "holidays" list, today is a holiday. If the file is missing or unreadable, fetch holidays/nyse_holidays.json from the technology-consults/cross-thread-task-status-tracker repo (@ main) via the GitHub API, save it to ~/workspace/shared/holidays/nyse_holidays.json, and use that copy going forward. Never rebuild the list from a web search; if the repo copy is unreachable too, do not guess — end the run with one brief failure note.
If any check fails, stay silent and end the run with no user-facing message.

Otherwise:
1. Run: python3 ~/workspace/repos/trading/src/build_scorecard.py > /tmp/scorecard.json
2. Read /tmp/scorecard.json — it contains {"post": true/false, "text": "..."}.
3. If post is true:
   a. From the "text" string, take the day from its first line (e.g. "Thu Oct 01") and the "Score: ..." line (e.g. "0 hit · 3 missed · 3 open · 6 scored"). Take the run's local time in America/Toronto and format it as "~h:MM AM/PM ET" (e.g. "~8:42 AM ET").
   b. Build the fixed-name PDF: python3 ~/workspace/repos/trading/src/build_scorecard_pdf.py ~/workspace/goals/etf-price-updates/hidden_files/signal_scorecard.json ~/workspace/goals/etf-price-updates/files/signal-scorecard.pdf --asof "<Day Mon DD> · <~h:MM AM/PM ET>" (e.g. --asof "Thu Oct 01 · ~8:42 AM ET")
      The PDF holds the FULL historic log of every scored signal as a table (newest published first); its title line shows the date AND time. The path is fixed — the file overwrites in place, so only the latest copy stays in artifacts.
   c. Your chat message is exactly one line — "📊 Signal scorecard · <Day Mon DD> · <~h:MM AM/PM ET> — <tally, e.g. 0 hit · 3 missed · 3 open · 6 scored>" — followed by the PDF on its own line:
      sandbox://workspace/goals/etf-price-updates/files/signal-scorecard.pdf
      Do not paste the signal table into the chat text; the full log lives in the PDF.
   d. Then run: python3 ~/workspace/repos/trading/src/build_scorecard.py --mark-posted
4. If post is false: stay silent and end the run with no user-facing message.

The ledger lives at ~/workspace/goals/etf-price-updates/hidden_files/signal_scorecard.json — the script maintains it; never edit it by hand. Score only signals the engine actually published; never invent or backfill signals, and never recompute the engine's targets.
