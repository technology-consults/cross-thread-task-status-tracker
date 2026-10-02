---
id: etf-trading-signals
title: ETF trading signals (QQQ, SPY, GLD)
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 07:30:00
delivery:
  - chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
metadata:
  originating_chat_context_json: '{"chat_id":"3c672068-efb2-446c-9e50-aa0a3d02adf1","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
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
5. Build the PDF report: run python3 ~/workspace/repos/trading/src/build_signals_pdf.py /tmp/etf_signal_out.json ~/workspace/goals/etf-price-updates/files/etf-signals-<YYYY-MM-DD>-<HHMM>-ET.pdf — build the filename from the run's local date and the asof time (e.g. etf-signals-2026-10-01-0735-ET.pdf). The PDF carries the full report: one bullet per symbol (signal, confidence, target, support/resistance, reasoning) plus key factors.
6. Your final chat message is exactly two lines: the one-line header "📊 Trading signals · <Day Mon DD> · <~h:MM AM/PM TZ> · Pre-market" (copy the asof from /tmp/etf_signal_out.json), then the PDF as an own-line sandbox link, e.g. [etf-signals-2026-10-01-0735-ET.pdf](sandbox://workspace/goals/etf-price-updates/files/etf-signals-2026-10-01-0735-ET.pdf). No prices or signal text in the chat message — the full report lives in the PDF.
7. After the message is sent, record state: re-run the build_signals.py command from step 4 with --update-state appended, so future runs can detect signal changes. If history or quotes genuinely cannot be obtained for a symbol, omit that symbol from the input rather than faking it, and say so in one short line after the PDF link.
