---
id: failure-log-weekly
title: Failure log weekly check
enabled: true
mode: task
schedule:
  kind: weekly
  timezone: America/Toronto
  time: 09:42:00
  dow: [Sat]
delivery:
  - surface: side_chat
    to: de5d7ab8-9709-4e7c-a556-fd5f582b2f7e
metadata:
  tags: [cron:flexible-time]
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"de5d7ab8-9709-4e7c-a556-fd5f582b2f7e","delivery_channel":"side_chat","delivery_target_id":"de5d7ab8-9709-4e7c-a556-fd5f582b2f7e","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Weekly accountability check for BalRam (created 2026-09-26 at his request — he wants the failure trend pushed to him, not something he has to remember to check).

Read ~/workspace/verifier/failures.md and send this chat exactly one short message:
- Current total entry count.
- Any entries dated within the last 7 days (date + one-line description each). If none: "no new entries this week."
No analysis, no promises, no process narration. Just the count.
