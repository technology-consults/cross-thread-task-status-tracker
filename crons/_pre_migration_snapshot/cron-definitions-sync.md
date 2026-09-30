---
id: cron-definitions-sync
title: Cron definitions sync to git
enabled: true
owner: goal:all-threads-status-board-upkeep
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
  time: 06:42:00
  timezone: America/Toronto
delivery:
- chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: daily@06:42:00
path: /home/hatch/workspace/goals/all-threads-status-board-upkeep/crons/daily/cron-definitions-sync__daily@06:42:00.md
is_heartbeat: false
is_system: false
---
Cron definitions backup + crons review page. Run `python3 ~/workspace/repos/cross-thread-task-status-tracker/scripts/sync_crons_to_git.py` — it copies every saved cron definition (`~/workspace/cron.d` and `~/workspace/goals/*/crons`) into the `crons/` directory of the `technology-consults/cross-thread-task-status-tracker` repo, rebuilds the review page `crons/index.html` (served by GitHub Pages at https://technology-consults.github.io/cross-thread-task-status-tracker/crons/), and commits via the GitHub API as a single commit, but only when something changed.

- On a no-change run, reply with exactly: no changes.
- If it committed, reply with one line: the commit sha and how many files changed.
- On any error, report the error briefly in this chat.
- Never create, edit, or delete any cron definition to "fix" a diff — this job mirrors the scheduler one-way; the scheduler is the source of truth.
