---
id: sv-build-driver
title: Build driver — one worker per run
enabled: true
owner: goal:short-video-creation-and-publishing-pipeline
mode: task
schedule:
  alignment: aligned
  at: 2026-09-30T09:30:00
  catchup: latest
  dom: []
  dow: []
  every: 3h
  kind: interval
  month: []
  time: null
  timezone: America/Toronto
delivery: []
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: interval@3h
path: /home/hatch/workspace/goals/short-video-creation-and-publishing-pipeline/crons/interval/sv-build-driver__interval@3h.md
is_heartbeat: false
is_system: false
---
The build-driver cron: reads program.py next for the top actionable BUILD item and spawns exactly one worker subagent per run to execute it. No human review needed (standing instruction).

1. Read the board task registry at ~/workspace/short-video/program/board_tasks_registry.json; the actionable queue is the set of tasks with status "agreed" or "building". For each, `program.py next` considers: dependencies met, not claimed by another coordinator (claimed: true means claimed by a human worker driver task). Take the top one (highest priority score, then oldest) that is not claimed.
2. If none is actionable, report "nothing to build" and stop. Do NOT start DEC/MANUAL items — those go to the poke stream.
3. Claim it: set "claimed": true and "claimed_by": "sv-build-driver <run date>", save the registry.
4. Spawn ONE worker subagent with a tight brief: repo paths, exact step to execute, the enforcement gate it must pass (build/run_from_git + regression before commit), and instructions to report back done/failed with the commit SHA.
5. When the worker reports done, mark the task done (or "in_review" with a review task created, per the task's review path); when failed, release the claim and log the failure to the goal timeline.

This cron itself never commits code — workers do, through the enforcement gate. One build at a time: this cron never spawns a second worker while the first is still active (check the program state lock).
