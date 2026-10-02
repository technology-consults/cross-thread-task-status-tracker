---
id: board-unblock-watch-tr
title: Board unblock watch — Trading
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Toronto
  at: 2026-09-29T20:58:03
  every: 6h
delivery:
  - chat_id: 1ff0cb94-8438-4900-8c47-a39846cbf1a3
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"1ff0cb94-8438-4900-8c47-a39846cbf1a3","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Board unblock watch for Trading tasks. Run `python3 ~/workspace/repos/cross-thread-task-status-tracker/unblock_watch.py --thread tr` — it prints a JSON list of trading board tasks that newly became actionable (blockers cleared or start date reached) and were never handled before.

For each task in the list:
- If the work is yours to do (drafting, research, building, configuring): do it now, then report the result briefly in this chat (the Trading task tracker). Ground yourself in the trading goal notes under ~/workspace/goals/ before acting.
- If the step is BalRam's (his account, his approval, something only he can do): send him one concise message here naming the task, why it is now unblocked, and exactly what his step is.
- After handling a task (work done or BalRam notified), append its id to the "handled" array in ~/workspace/repos/cross-thread-task-status-tracker/hidden_files/unblock_watch_state.json so it never fires twice. Read-modify-write carefully to preserve existing entries.

Pickup sweep (idle + stalled + stuck-completed tasks). After the unblock check, run `python3 ~/workspace/repos/cross-thread-task-status-tracker/unblock_watch.py --thread tr --sweep` — it prints tasks the unblock check never re-surfaces, each with a "reason" and an "owner_hint":
- reason "idle": todo with blockers already clear but never handled — a pickup that was missed.
- reason "stalled": in_progress with no update in 3+ days (recurring/standing work excluded) — report only, never auto-act.
- reason "completed_stalled": completed with no update since an earlier day — post-review actions should finish the same day, so this means the automation failed or stalled — report only, never auto-act.

For each task in the sweep list:
- reason idle and the work is yours: do it now, report the result briefly in this chat (the Trading task tracker), then mark handled.
- reason idle and the step is BalRam's: send him one concise message naming the task and his step, then mark handled.
- reason stalled: do NOT start or change anything, and NEVER mark stalled ids handled — they stay visible so the watcher keeps reminding until a decision (a status change) resolves them. Send the brief note (task name, last-update date, owner hint) at most once per 24h per task: keep a "stalled_reminded" map of id → ISO timestamp in ~/workspace/repos/cross-thread-task-status-tracker/hidden_files/unblock_watch_state.json; if the id was reminded within the last 24h, stay silent for it; otherwise send the note and record the current UTC timestamp. Read-modify-write carefully to preserve existing entries.
- reason completed_stalled: do NOT start or change anything. Send a brief note here naming the task and its last-update date, then mark handled.

Append handled ids to ~/workspace/repos/cross-thread-task-status-tracker/hidden_files/unblock_watch_state.json with the same read-modify-write care.

Task digests: watchers never generate or send digests (BalRam's locked rule 2026-09-28). Digests are produced only after board publishes via push_board.py.

Rules:
- Only act on tasks in the scripts' outputs. Never start other tasks.
- Empty outputs: stay silent, send nothing.
- If a task cannot be completed or this run hits an error, report the blocker/failure briefly in this chat rather than staying silent.
- Never edit task statuses directly in tasks.json; status changes go through the board flow (push_board.py).
