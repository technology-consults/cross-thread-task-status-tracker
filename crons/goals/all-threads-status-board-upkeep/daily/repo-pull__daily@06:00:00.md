---
id: repo-pull
title: Repo workbench pull
enabled: true
owner: goal:all-threads-status-board-upkeep
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 06:00:00
delivery:
  - chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
metadata:
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Repo workbench sync. Run `bash ~/workspace/repos/cross-thread-task-status-tracker/scripts/pull_all_repos.sh` — it fetches origin/main for every clone under ~/workspace/repos/ and fast-forwards the clean ones. Repos with uncommitted local changes are SKIPPED, never overwritten; repos that cannot fast-forward are reported, not forced.

- Reply with one line per repo: OK (already current), PULLED, SKIP (with reason), or FAIL (with the error text).
- Never use reset --hard or otherwise discard local changes. Never commit anything.
- This job only updates the local workbench; it never touches the scheduler or any repo's remote.
