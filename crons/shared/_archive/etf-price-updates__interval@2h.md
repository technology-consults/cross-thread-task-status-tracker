---
id: etf-price-updates
title: ETF price updates (QQQ, SPY, GLD)
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Toronto
  at: 2026-09-21T10:00:00
  every: 2h
metadata:
  predicted_connector_permissions:
  - connector: gmail
    method: users.messages.send
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Price update for QQQ, SPY, and GLD, with per-symbol charts. BalRam's standing format: three stacked theme-aware cards, one per symbol (see step 4) — keep this format for all future alerts.

First, decide whether this run should report. Get the current local time in America/Toronto. Only report if ALL of these hold:
1. Today is Monday–Friday.
2. The local time is between 08:00 and 16:00 inclusive.
3. Today is a NYSE trading day (not a US stock market holiday — if unsure, do a quick web search for the NYSE holiday calendar for the current year).

If any check fails, stay silent and end the run with no user-facing message.

Otherwise:
1. Use browser_search with the finance vertical to get the current price of QQQ, SPY, and GLD, plus each one's change today in points and percent. Note whether the market is open or the quote is pre-market. Use one as-of timestamp across all three.
2. Get chart history per symbol at the best available horizon, and LABEL each chart with its exact period and date range:
   - ALL THREE symbols (QQQ, SPY, GLD): TWO charts each — 1 month of daily closes (~20 trading days) AND 3 months of daily closes (~63 trading days), both ending the most recent Friday's close. The finance vertical's daily candles reliably return QQQ (verified 2026-09-21); verify the returned entity's symbol is exactly QQQ. For SPY/GLD the finance vertical sometimes returns lookalike symbols (SPYQ/YSPY/DVSP for SPY; GLDI/GSGO/GPIX/GLDB for GLD) — verify the symbol matches exactly and keep trying; if it fails, use a live browser task reading Nasdaq's historical-data tables (nasdaq.com/market-activity/stocks/<ticker>/historical): the timeframe selector offers 1M/6M/YTD/1Y/5Y/MAX with no 3M option, so for 3 months use the 6M range and take the last ~63 trading days, and for 1 month use the 1M range directly (verified working 2026-09-21). If a period genuinely cannot be obtained for a symbol, fall back to the available period for that symbol. Never invent or interpolate history: if a symbol's history genuinely cannot be obtained this run, mark that symbol's chart unavailable rather than faking it.
3. Economic-event dates: charts must mark CPI, PPI, FOMC-decision, and jobs (NFP) release dates that fall in each chart window. Read ~/workspace/etf-alerts/econ_events.json — if the chart windows need release dates beyond its coverage (or a listed date looks stale), search the web for the official dates (BLS release schedules for CPI/PPI/Employment Situation; the Federal Reserve's FOMC meeting calendar, decision = second day) and update the file before building. Never guess a release date.
4. Hand off to the main agent with: one line per symbol (symbol, current price, today's point and percent change), the market-open note, the period used per symbol (e.g. {"QQQ": ["1M", "3M"], "SPY": ["1M", "3M"], "GLD": ["1M", "3M"]}), and a CHART_DATA JSON block on its own lines: {"QQQ_1M": [["YYYY-MM-DD", close], ...], "QQQ_3M": [...], "SPY_1M": [...], "SPY_3M": [...], "GLD_1M": [...], "GLD_3M": [...]} with daily closes oldest to newest. Omit any symbol whose history is unavailable (do not write CHART_DATA: unavailable for the whole block when only one symbol failed).
5. The final chat message is a theme-aware HTML widget with THREE stacked cards, one per symbol. Build it by writing /tmp/etf_widget_input.json with {"asof": "<Day Mon DD> · <~h:MM AM/PM TZ> · Market open|Market closed", "quotes": {"QQQ": {"name": "Invesco QQQ Trust", "color": "#3b82f6", "price": <current>, "change": <pts>, "pct": <pct>}, "SPY": {"name": "SPDR S&P 500 ETF Trust", "color": "#10b981", ...}, "GLD": {"name": "SPDR Gold Shares", "color": "#d97706", ...}}, "charts": {"QQQ": [{"period": "1M", "note": "Daily closes, <Mon DD> – <Mon DD>, <YYYY> (1 month)", "data": [...]}, {"period": "3M", ...}], "SPY": [...], "GLD": [...]}} using the exact quotes, notes, and CHART_DATA from step 4, then run: python3 ~/workspace/etf-alerts/build_widget.py /tmp/etf_widget_input.json /tmp/etf_widget.html — and present /tmp/etf_widget.html with the widget tool. Each card contains: a header (ticker + full name, big current price, day-change pill in green #16a34a for up / red #dc2626 for down), the symbol's charts — each symbol shows BOTH its 1-month and 3-month daily-close charts stacked (distinct strong color per symbol: QQQ #3b82f6 blue, SPY #10b981 green, GLD #d97706 amber; 3px line, gradient area fill, high/low markers, date labels; high-contrast gridlines and muted labels; each chart notes its exact period and date range, e.g. "Daily closes, Jun 22 – Sep 18, 2026 (3 months)", and that the header price is intraday while charts end at Friday's close; CPI/PPI/FOMC/NFP release dates in the window are drawn automatically as vertical dashed violet lines with labels, from econ_events.json), and a compact stats table with one row per chart period showing the period change (e.g. "3M change +$17.30 (+2.32%)") — no high/low rows (already marked on the chart) and no prev-close row. For symbols whose history is unavailable, show prev close / 52wk range instead with a small honest "chart unavailable, retrying next update" note in place of the chart. Keep prose minimal.
6. Also email this same alert as HTML to balram.bandhu.finance@gmail.com. Write /tmp/etf_email_input.json with the same shape as the widget input in step 5 (subject: "ETF update · <Day Mon DD, YYYY>"), then run: python3 ~/workspace/etf-alerts/build_and_send_email.py /tmp/etf_email_input.json — it renders the charts (with the same econ-event markers, via econ_events.json) as inline PNG images (Gmail strips SVG) and sends via the connected Gmail account (send scope granted; verified working 2026-09-21). If the send fails, retry once; if it still fails, report the failure in chat.
