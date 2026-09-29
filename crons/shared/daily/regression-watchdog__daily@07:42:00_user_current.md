---
id: regression-watchdog
title: Daily regression watchdog
enabled: false
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 07:42:00
delivery:
  - chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
# Daily regression watchdog — runs all regression suites, alerts on failure.

Run: `python3 /home/hatch/workspace/repos/cross-thread-task-status-tracker/tests/run_all.py`

Capture the output and exit code.

If exit code is 0: stay silent (all green). No chat message.

If exit code is non-zero:
- Send a brief alert to the Main chat listing which suite failed and the failing check names.
- Do NOT attempt to fix — just report. Fixes follow the normal review flow.

This is the safety net: even if a deploy somehow bypasses its gate, this catches the breakage within 24 hours.
