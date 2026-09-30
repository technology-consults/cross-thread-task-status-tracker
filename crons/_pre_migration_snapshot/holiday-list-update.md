---
id: holiday-list-update
title: NYSE holiday list quarterly refresh
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  alignment: aligned
  at: null
  catchup: latest
  dom:
  - 1
  dow: []
  every: null
  kind: monthly
  month: []
  time: 20:00:00
  timezone: America/Toronto
delivery:
- chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: monthly@1-20:00:00
path: /home/hatch/workspace/goals/etf-price-updates/crons/monthly/holiday-list-update__monthly@1-20:00:00.md
is_heartbeat: false
is_system: false
---
Quarterly NYSE/Nasdaq holiday calendar refresh — keep this run FAST: fetch only the next four calendar months, nothing more. You are the ONLY writer of the shared holiday list — no other job touches it. Chat delivery only on failure or source disagreement — never email. DEFAULT IS SILENCE on success.

1. The window is the next four calendar months starting with the current month (an October 1 run covers October–January; a January 1 run covers January–April). Extract every FULL-DAY market closure (ignore early-close days) inside that window — nothing outside it.
2. Fetch the official NYSE holiday calendar (NYSE Group announcement: https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/default.aspx) and the Nasdaq-published copy of the same NYSE calendar (https://www.nasdaq.com/press-release/nyse-group-announces-2025-2026-and-2027-holiday-and-early-closings-calendar-2024-11). If the Nasdaq copy does not cover the full window, find the current Nasdaq publication of the NYSE holiday calendar that does (same press-release series) and use that instead — never cross-check against a source that does not cover the window.
3. Cross-check: both sources must agree on every date in the window. If they disagree on any date, do NOT guess and do NOT write anything — send a brief chat message flagging the disagreement (which date, what each source says) and end.
4. Write ~/workspace/shared/holidays/nyse_holidays.json: {"updated": "<today as YYYY-MM-DD>", "sources": ["<NYSE url used>", "<Nasdaq url used>"], "note": "Full-day NYSE closures (YYYY-MM-DD) for the next four calendar months (<Mon YYYY>–<Mon YYYY>). Single source of truth, maintained ONLY by the holiday-list-update cron (quarterly, 1st of Jan/Apr/Jul/Oct).", "holidays": ["YYYY-MM-DD", ...]} — dates sorted ascending, covering ONLY the next four calendar months.
5. Run: python3 ~/workspace/repos/cross-thread-task-status-tracker/scripts/sync_holiday_copies.py — this validates the file and mirrors it one-way to the cross-thread repo (holidays/nyse_holidays.json @ main). It touches NOTHING else. If it fails, send a brief chat message describing what failed.
6. On success: stay completely silent — no chat message, no report.

Copy rules (standing): the workspace copy is the authoritative local copy — all local logic and scripts work from it. If it is ever missing, pull holidays/nyse_holidays.json from the technology-consults/cross-thread-task-status-tracker repo (@ main) into the workspace first, then proceed. Never reconstruct the list from a web search.

IMPORTANT: this job never writes the trading portal. The portal deployable is assembled separately by the portal deploy script, which pulls this JSON from the cross-thread repo at deploy time.
