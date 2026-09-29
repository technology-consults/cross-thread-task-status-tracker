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
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Weekday market-hours data refresh for the ETF live page at workspace/your_files/etf-live.html (the page BalRam opens from his Artifacts tab; the file already lives there at his request — this job only refreshes its embedded data bundle, it creates no new files).

1. Get the current time in America/New_York: run `TZ=America/New_York date +%u-%H%M` (gives weekday number 1-7 and HHMM).
2. If it is NOT a weekday (Mon-Fri, i.e. first number 1-5) or the time is outside 04:00-21:00 ET, do nothing and stay completely silent. Also read ~/workspace/shared/holidays/nyse_holidays.json — if today's date (YYYY-MM-DD) is in the "holidays" list, today is a NYSE holiday: do nothing and stay completely silent (no bake, no push — the page already labels holidays "Market closed" from the same list). If the file is missing or unreadable, fetch holidays/nyse_holidays.json from the technology-consults/cross-thread-task-status-tracker repo (@ main) via the GitHub API, save it to ~/workspace/shared/holidays/nyse_holidays.json, and use that copy going forward. Never rebuild the list from a web search; if the repo copy is unreachable too, do not guess — end the run with one brief failure note.
3. Otherwise run: `python3 /home/hatch/workspace/repos/trading/src/build_live_bundle.py`
4. On success: stay silent — no chat message, no report.
5. On failure: append the timestamped error to workspace/goals/etf-price-updates/hidden_files/etf_live_bundle.log (create the directory if needed) and send one brief chat message noting the bundle refresh failed and the page keeps showing its last baked data.
