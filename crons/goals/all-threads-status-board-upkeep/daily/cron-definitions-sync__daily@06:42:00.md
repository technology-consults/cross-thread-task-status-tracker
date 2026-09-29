---
id: cron-definitions-sync
title: Cron definitions sync to git
enabled: true
owner: goal:all-threads-status-board-upkeep
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 06:42:00
delivery:
  - chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Cron definitions backup. Run `python3 ~/workspace/repos/cross-thread-task-status-tracker/scripts/sync_crons_to_git.py` — it copies every saved cron definition (`~/workspace/cron.d` and `~/workspace/goals/*/crons`) into the `crons/` directory of the `technology-consults/cross-thread-task-status-tracker` repo and commits via the GitHub API as a single commit, but only when something changed.

- On a no-change run, reply with exactly: no changes.
- If it committed, reply with one line: the commit sha and how many files changed.
- On any error, report the error briefly in this chat.
- Never create, edit, or delete any cron definition to "fix" a diff — this job mirrors the scheduler one-way; the scheduler is the source of truth.
