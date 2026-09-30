---
id: sv-chat-review
title: Daily per-chat review (short-video)
enabled: true
owner: goal:short-video-creation-and-publishing-pipeline
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
delivery: []
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: daily@07:42:00
path: /home/hatch/workspace/goals/short-video-creation-and-publishing-pipeline/crons/daily/sv-chat-review__daily@07:42:00_user_current.md
is_heartbeat: false
is_system: false
---
Daily per-chat review for the short-video project: read each configured project chat's recent messages and check for signs of stalls, blockers, or user questions that went unanswered. Report to the Main chat only when there IS something to flag; stay silent otherwise.

Chats to review (chat ids):
- Short Video chat: chat id is in the sv config (~/workspace/short-video/program/sv_config.json, key chat_id).
- Short Video publisher chat: in the publisher program dir (~/workspace/short-video-publisher/program/config.json, key chat_id).
- For review thread: b95fb15f-a58f-4547-b9cd-cdce882a5cd9.

Look at the last 24 hours of each chat. Flag:
- A user question that received no agent reply within 2 hours.
- A builder/runner reporting a blocking error that was never resolved.
- Anything that looks stalled (last agent activity > 12 hours ago with the task not marked done).

Then check the task registry at ~/workspace/short-video/program/board_tasks_registry.json — for any task marked "blocked" with a linked blocker thread, make sure a review task or poke exists for it; if a blocker has been silent for 3+ days, flag it.

If nothing to flag: stay silent. Do not post summaries.

Rules: never write to MEMORY.md (observations go to ~/memory/YYYY-MM-DD.md). Never modify tasks — this job is read-only except for its own log entries. This job never publishes anything and never touches platform APIs.
