---
id: failure-log-weekly
title: Failure log weekly check
enabled: true
owner: null
mode: task
schedule:
  alignment: aligned
  at: null
  catchup: latest
  dom: []
  dow:
  - Sat
  every: null
  kind: weekly
  month: []
  time: 09:42:00
  timezone: America/Toronto
delivery:
- chat_id: de5d7ab8-9709-4e7c-a556-fd5f582b2f7e
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: weekly@Sat-09:42:00
path: /home/hatch/workspace/cron.d/weekly/failure-log-weekly__weekly@Sat-09:42:00.md
is_heartbeat: false
is_system: false
---
Weekly accountability check for BalRam (created 2026-09-26 at his request — he wants the failure trend pushed to him, not something he has to remember to check).

Read ~/workspace/verifier/failures.md and send this chat exactly one short message:
- Current total entry count.
- Any entries dated within the last 7 days (date + one-line description each). If none: "no new entries this week."
No analysis, no promises, no process narration. Just the count.
