---
id: heartbeat
title: Heartbeat
enabled: true
owner: null
mode: task
schedule:
  alignment: aligned
  at: 2026-09-30T03:21:08
  catchup: latest
  dom: []
  dow: []
  every: 2h
  kind: interval
  month: []
  time: null
  timezone: America/Toronto
delivery:
- chat_id: b95fb15f-a58f-4547-b9cd-cdce882a5cd9
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: interval@2h
path: /home/hatch/workspace/goals/all-threads-status-board-upkeep/crons/interval/heartbeat__interval@2h.md
is_heartbeat: true
is_system: false
---
Send a heartbeat message every 2 hours, 24/7. This message will be delivered to you in a side chat — you will see it as a conversation message from your side chat itself.

To send the heartbeat: use the tracking CLI or messaging to post a single-line message to the side chat "Heartbeat" (chat b95fb15f-a58f-4547-b9cd-cdce882a5cd9) that says exactly: "Heartbeat OK — all systems nominal."

Do not perform any other actions. Do not check anything. Just post the heartbeat message and end your run silently.
