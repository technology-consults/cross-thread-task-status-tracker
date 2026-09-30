---
id: regression-watchdog
title: Daily regression watchdog
enabled: false
owner: null
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
  time: 07:42:00
  timezone: "@user.current"
delivery:
- chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: daily@07:42:00
path: /home/hatch/workspace/cron.d/daily/regression-watchdog__daily@07:42:00_user_current.md
is_heartbeat: false
is_system: false
---
# Daily regression watchdog — runs all regression suites, alerts on failure.

Run: `python3 /home/hatch/workspace/repos/cross-thread-task-status-tracker/tests/run_all.py`

Capture the output and exit code.

If exit code is 0: stay silent (all green). No chat message.

If exit code is non-zero:
- Send a brief alert to the Main chat listing which suite failed and the failing check names.
- Do NOT attempt to fix — just report. Fixes follow the normal review flow.

This is the safety net: even if a deploy somehow bypasses its gate, this catches the breakage within 24 hours.
