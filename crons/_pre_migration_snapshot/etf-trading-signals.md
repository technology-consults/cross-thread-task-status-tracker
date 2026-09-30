---
id: etf-trading-signals
title: ETF trading signals (QQQ, SPY, GLD)
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
  time: 07:30:00
  timezone: America/Toronto
delivery:
- chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: daily@07:30:00
path: /home/hatch/workspace/goals/etf-price-updates/crons/daily/etf-trading-signals__daily@07:30:00.md
is_heartbeat: false
is_system: false
---
Daily trading-signal report for QQQ, SPY, and GLD, delivered to the Trading chat alongside the 8:00 AM ETF update. Chat delivery only — never email. Signals come from the rule-based engine in ~/workspace/repos/trading/src/build_signals.py (technical trend/momentum + macro factors) and are informational only, not financial advice — the message footer says so; never present them as advice or guarantees.

First, decide whether this run should report. Get the current local date and time in America/Toronto. Only proceed if ALL of these hold:
1. Today is Monday–Friday.
2. Today is a NYSE trading day — read ~/workspace/shared/holidays/nyse_holidays.json; if today's date (YYYY-MM-DD) is in the "holidays" list, today is a holiday. If the file is missing or unreadable, fetch holidays/nyse_holidays.json from the technology-consults/cross-thread-task-status-tracker repo (@ main) via the GitHub API, save it to ~/workspace/shared/holidays/nyse_holidays.json, and use that copy going forward. Never rebuild the list from a web search; if the repo copy is unreachable too, do not guess — end the run with one brief failure note.
If any check fails, stay silent and end the run with no user-facing message.

Otherwise:
1. Get price history per symbol FIRST — this is the slow step, so do it before quotes to keep prices fresh. For ALL THREE symbols (QQQ, SPY, GLD): ~6 months of daily closes (last ~130 trading days) via a live browser task reading Nasdaq's historical-data tables (nasdaq.com/market-activity/stocks/<ticker>/historical) with the 6M timeframe. The finance vertical's daily candles also work for QQQ (verify the returned entity's symbol is exactly QQQ); for SPY/GLD the finance vertical returns lookalike symbols, so prefer Nasdaq tables. Diff the SPY date list against QQQ/GLD and drop SPY phantom holiday rows (Nasdaq prints plausible-looking non-trading rows on NYSE holidays). Never invent or interpolate history.
2. Gather macro factors via browser_search (news vertical), about 5 queries: (a) Federal Reserve / FOMC interest-rate latest; (b) CPI inflation latest — also read ~/workspace/repos/trading/src/econ_events.json for upcoming CPI/PPI release dates and treat a release within 3 days as event-risk; (c) US jobs report / unemployment latest; (d) S&P 500 / Nasdaq market news today (trend, VIX); (e) gold price news — geopolitical/war developments and safe-haven demand, US dollar index, Treasury yields, central-bank gold buying. Record each factor with: name, direction (1 bullish / -1 bearish / 0 neutral for the assets it applies to), weight 1–3, one-line note, applies_to (["ALL"] or specific symbols — war/safe-haven/dollar/yield/central-bank factors usually apply to ["GLD"] unless they clearly move equities too), and major=true ONLY for genuinely market-moving events (rate-decision surprise, CPI shock, major war escalation, emergency Fed action).
3. LAST, right before building: fetch current pre-market quotes — finance vertical for QQQ (verify symbol exactly QQQ); stockanalysis.com/etf/<ticker>/history/ for SPY/GLD, which shows the live pre-market value during pre-market hours. The asof session is "Pre-market". Take one as-of timestamp for all three.
4. Write /tmp/etf_signal_input.json: {"asof": "<Day Mon DD> · <~h:MM AM/PM TZ> · Pre-market", "session": "Pre-market", "symbols": {"QQQ": {"price": <pre-mkt>, "prev_close": <prev close>, "history": [["YYYY-MM-DD", close], ...]}, "SPY": {...}, "GLD": {...}}, "macro": {"factors": [...]}}. Then run: python3 ~/workspace/repos/trading/src/build_signals.py /tmp/etf_signal_input.json /tmp/etf_signal_out.json --mode morning --state ~/workspace/goals/etf-price-updates/hidden_files/etf_signal_state.json
5. Your final chat message is EXACTLY the "message" string from /tmp/etf_signal_out.json — post it verbatim, no added text, no prices repeated outside it.
6. After the message is sent, record state: re-run the same script command with --update-state appended, so future runs can detect signal changes. If history or quotes genuinely cannot be obtained for a symbol, omit that symbol from the input rather than faking it, and say so in one short line appended after the message.
