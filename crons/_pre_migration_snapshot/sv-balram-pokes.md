---
id: sv-balram-pokes
title: Review pokes to BalRam (For review thread)
enabled: true
owner: goal:short-video-creation-and-publishing-pipeline
mode: task
schedule:
  alignment: aligned
  at: 2026-09-30T13:00:00
  catchup: latest
  dom: []
  dow: []
  every: 5h
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
schedule_key: interval@5h
path: /home/hatch/workspace/goals/short-video-creation-and-publishing-pipeline/crons/interval/sv-balram-pokes__interval@5h.md
is_heartbeat: false
is_system: false
---
Poke BalRam in the "For review" thread (chat b95fb15f-a58f-4547-b9cd-cdce882a5cd9) about short-video items still awaiting his review. Max 3 pokes per item, then STOP (never poke a fourth time) — even for urgent items. This cron runs daily at 8 AM and 6 PM ET; other daily crons respect this 3-poke cap on your behalf.

This job never touches platform APIs and never publishes anything — review-poking only.

1. Read the board tasks registry from ~/workspace/short-video/program/board_tasks_registry.json (or the goal's board area) — find open tasks with `review: pending` (or `status: pending_review`) that are assigned to BalRam (his name or id).
2. For each, read the task's `poke_count` (default 0). If `poke_count` >= 3, SKIP it — do not poke again.
3. For each task with `poke_count` < 3: post a poke in the For review thread: "<task title> still needs your review: <link to task or brief description>".
4. After all pokes, increment `poke_count` for each poked task in the registry. Persist the update.
5. If there is nothing to poke, stay silent.

Rules: never write to MEMORY.md (observations go to ~/memory/YYYY-MM-DD.md). If the registry is missing or unreadable, report the failure once in this run's message instead of poking blind.
