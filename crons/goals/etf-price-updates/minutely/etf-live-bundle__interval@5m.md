---
id: etf-live-bundle
title: ETF live page data bundle refresh
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  kind: interval
  timezone: America/Toronto
  at: 2026-09-26T00:02:31
  every: 5m
timeout_secs: 120
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Weekday market-hours data refresh for the ETF live page at workspace/your_files/etf-live.html (the page BalRam opens from his Artifacts tab; the file already lives there at his request — this job only refreshes its embedded data bundle, it creates no new files).

1. Get the current time in America/New_York: run `TZ=America/New_York date +%u-%H%M` (gives weekday number 1-7 and HHMM).
2. If it is NOT a weekday (Mon-Fri, i.e. first number 1-5) or the time is outside 04:00-21:00 ET, do nothing and stay completely silent.
3. Otherwise run: `python3 /home/hatch/workspace/repos/trading/src/build_live_bundle.py`
4. On success: stay silent — no chat message, no report.
5. On failure: append the timestamped error to workspace/goals/etf-price-updates/hidden_files/etf_live_bundle.log (create the directory if needed) and send one brief chat message noting the bundle refresh failed and the page keeps showing its last baked data.
