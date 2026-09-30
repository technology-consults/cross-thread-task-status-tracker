---
id: repo-pull
title: Repo workbench pull
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
  time: 06:00:00
  timezone: America/Toronto
delivery:
- chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: daily@06:00:00
path: /home/hatch/workspace/goals/all-threads-status-board-upkeep/crons/daily/repo-pull__daily@06:00:00.md
is_heartbeat: false
is_system: false
---
Repo workbench sync. Run `bash ~/workspace/repos/cross-thread-task-status-tracker/scripts/pull_all_repos.sh` — it fetches origin/main for every clone under ~/workspace/repos/ and fast-forwards the clean ones. Repos with uncommitted local changes are SKIPPED, never overwritten; repos that cannot fast-forward are reported, not forced.

- Reply with one line per repo: OK (already current), PULLED, SKIP (with reason), or FAIL (with the error text).
- Never use reset --hard or otherwise discard local changes. Never commit anything.
- This job only updates the local workbench; it never touches the scheduler or any repo's remote.
