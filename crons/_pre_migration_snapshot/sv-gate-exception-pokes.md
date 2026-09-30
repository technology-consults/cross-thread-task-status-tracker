---
id: sv-gate-exception-pokes
title: Hourly gate-exception pokes
enabled: true
owner: goal:short-video-creation-and-publishing-pipeline
mode: task
schedule:
  alignment: aligned
  at: 2026-09-30T08:00:00
  catchup: latest
  dom: []
  dow: []
  every: 1h
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
schedule_key: interval@1h
path: /home/hatch/workspace/goals/short-video-creation-and-publishing-pipeline/crons/interval/sv-gate-exception-pokes__interval@1h.md
is_heartbeat: false
is_system: false
---
Hourly poke stream for prod-critical gate exceptions. Poke BalRam in the "For review" thread (chat b95fb15f-a58f-4547-b9cd-cdce882a5cd9) about open gate-exception approval tasks that are blocking production-critical work. NO 3-poke cap on these — hourly until resolved (his explicit override for prod-critical, 2026-09-30).

1. Read the board tasks registry from ~/workspace/short-video/program/board_tasks_registry.json — find open tasks with status pending_review, assigned to BalRam, and priority prod-critical.
2. For each such task: post a poke in the For review thread: "<task title> still blocks prod-critical work — needs your approval: <link or brief description>".
3. If there is nothing to poke, stay silent.

Rules: never write to MEMORY.md (observations go to ~/memory/YYYY-MM-DD.md). This job never commits code and never touches platform APIs — poking only.
