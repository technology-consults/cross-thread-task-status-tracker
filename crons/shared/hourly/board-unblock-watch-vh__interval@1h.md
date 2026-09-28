---
id: board-unblock-watch-vh
title: Board unblock watch — Vehicle
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Toronto
  at: 2026-09-27T22:50:13
  every: 1h
delivery:
  - chat_id: 547fb3d1-6b69-4410-b9d0-084cd478e7ff
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Board unblock watch for Vehicle tasks. Run `python3 ~/workspace/repos/cross-thread-task-status-tracker/unblock_watch.py --thread vh` — it prints a JSON list of vehicle board tasks that newly became actionable (blockers cleared or start date reached) and were never handled before.

For each task in the list:
- If the work is yours to do (drafting, research, building, configuring): do it now, then report the result briefly in this chat (the Vehicle task tracker). Ground yourself in the vehicle goal notes under ~/workspace/goals/ before acting.
- If the step is BalRam's (his account, his approval, something only he can do): send him one concise message here naming the task, why it is now unblocked, and exactly what his step is.
- After handling a task (work done or BalRam notified), append its id to the "handled" array in ~/workspace/repos/cross-thread-task-status-tracker/hidden_files/unblock_watch_state.json so it never fires twice. Read-modify-write carefully to preserve existing entries.

Pickup sweep (idle + stalled tasks). After the unblock check, run `python3 ~/workspace/repos/cross-thread-task-status-tracker/unblock_watch.py --thread vh --sweep` — it prints tasks the unblock check never re-surfaces, each with a "reason" and an "owner_hint":
- reason "idle": todo with blockers already clear but never handled — a pickup that was missed.
- reason "stalled": in_progress with no update in 3+ days (recurring/standing work excluded) — report only, never auto-act.

For each task in the sweep list:
- reason idle and the work is yours: do it now, report the result briefly in this chat (the Vehicle task tracker), then mark handled.
- reason idle and the step is BalRam's: send him one concise message naming the task and his step, then mark handled.
- reason stalled: do NOT start or change anything. Send a brief note here naming the task, its last-update date, and the owner hint, then mark handled.

Append handled ids to ~/workspace/repos/cross-thread-task-status-tracker/hidden_files/unblock_watch_state.json with the same read-modify-write care.

Pending-tasks digest (only when this run posted updates). If you sent any task status-change update to this tracker thread in this run (unblock notice, sweep pickup, or stalled report), finish with the pending-tasks digest:
- Run `~/workspace/.docbuild-venv/bin/python ~/workspace/repos/cross-thread-task-status-tracker/scripts/pending_digest.py --thread vh`. It prints a markdown table of ALL pending tasks for this thread (every status except agreed/rejected: blocked, pending review, pending from me, in progress, to-do, parked) and writes a timestamped PDF named vehicle-pending-tasks-<timestamp>.pdf to ~/workspace/your_files/task-tracker-digests/vehicle/, deleting older copies so only the latest PDF is kept.
- Post the printed table in this tracker thread after the updates, then attach the PDF from the PDF_PATH line (same list as the message).
- If this run posted no updates (empty unblock + sweep outputs, stayed silent), skip the digest entirely. The digest rides along with updates; it never fires on its own.

Rules:
- Only act on tasks in the scripts' outputs. Never start other tasks.
- Empty outputs: stay silent, send nothing.
- If a task cannot be completed or this run hits an error, report the blocker/failure briefly in this chat rather than staying silent.
- Never edit task statuses directly in tasks.json; status changes go through the board flow (push_board.py).
