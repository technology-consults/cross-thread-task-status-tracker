---
id: holiday-list-update
title: NYSE holiday list weekly refresh
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  kind: weekly
  timezone: America/Toronto
  time: 20:00:00
  dow: [Sun]
delivery:
  - chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
metadata:
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Weekly NYSE/Nasdaq holiday calendar refresh. You are the ONLY writer of the shared holiday list — no other job touches it. Chat delivery only on failure or source disagreement — never email. DEFAULT IS SILENCE on success.

1. Fetch the official NYSE holiday calendar (NYSE Group announcement: https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/default.aspx) and the Nasdaq-published copy of the same NYSE calendar (https://www.nasdaq.com/press-release/nyse-group-announces-2025-2026-and-2027-holiday-and-early-closings-calendar-2024-11). Extract every FULL-DAY market closure (ignore early-close days) for the full calendar years 2026, 2027, and 2028.
2. Cross-check: both sources must agree on every date. If they disagree on any date, do NOT guess and do NOT write anything — send a brief chat message flagging the disagreement (which date, what each source says) and end.
3. Write ~/workspace/shared/holidays/nyse_holidays.json: {"updated": "<today as YYYY-MM-DD>", "sources": ["<NYSE url used>", "<Nasdaq url used>"], "note": "<one-line note>", "holidays": ["YYYY-MM-DD", ...]} — dates sorted ascending, covering full calendar years 2026–2028 (past dates stay in the list; extend the year range only when a newer official NYSE calendar is published). Keep the note's "single source of truth, maintained ONLY by the holiday-list-update cron" wording.
4. Run: python3 ~/workspace/shared/holidays/sync_holiday_copies.py — this validates the file and mirrors it to the cross-thread repo (holidays/nyse_holidays.json @ main). It touches NOTHING else. If it fails, send a brief chat message describing what failed.
5. On success: stay completely silent — no chat message, no report.

IMPORTANT: this job never writes the trading portal. The portal deployable is assembled separately by the portal deploy script, which pulls this JSON from the cross-thread repo at deploy time.
