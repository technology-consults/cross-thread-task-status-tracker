---
id: job-watchdog
title: Scheduled job watchdog
enabled: true
owner: goal:job-watchdog-for-scheduled-jobs
mode: task
schedule:
  kind: interval
  timezone: America/Toronto
  at: 2026-09-25T20:28:44
  every: 1h
timeout_secs: 300
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
You are the scheduled-job watchdog. Check the health of BalRam's six scheduled jobs and report ONLY problems. Stay silent when everything is healthy.

Jobs to watch (use cron.runs and cron.status):
1. etf-price-updates (every ~2h)
2. etf-price-preclose (daily ~15:00 ET)
3. etf-trading-signals (daily ~07:30 ET)
4. etf-signal-intraday (every ~2h)
5. phev-ev-suv-deal-watch (daily ~08:00 ET)
6. precon-digest (daily ~08:42 ET) — CURRENTLY DISABLED (see below)

Skip any job whose schedule is currently disabled (check enabled via cron.status): a disabled job is intentional, not a problem — do not flag its lack of runs. (precon-digest was disabled 2026-09-26 per BalRam until he asks to reactivate.)

For each remaining job, look at its most recent runs:
- If the latest run FAILED (error status), that is a problem — report it.
- If there is no completed run within the expected window, that is a missed run — report it. Windows: interval jobs 3 hours, daily jobs 30 hours. NOTE: these jobs only do real work on NYSE trading days. On weekends (and market holidays), extend the windows to 3 days (Friday's runs cover the weekend), and a run that completed quietly because it was not a trading day counts as healthy — do not flag it.

How to report: end your run with a clear summary. If all watched jobs are healthy, write exactly "Watchdog: all scheduled jobs healthy." — nothing needs to reach the user. If anything is wrong, list each problem with the job id, last run time, status, and error text, plus whether it looks transient or needs attention.

Do not attempt to fix anything yourself and do not modify any schedule. Detection and reporting only. Write any notable observations to the daily log at ~/memory/YYYY-MM-DD.md (never edit MEMORY.md directly).
