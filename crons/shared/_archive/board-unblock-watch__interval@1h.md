---
id: board-unblock-watch
title: Board unblock watch
enabled: true
mode: task
schedule:
  kind: interval
  timezone: America/Toronto
  at: 2026-09-27T22:48:11
  every: 1h
delivery:
  - surface: side_chat
    to: 9c6459ad-00f6-47e3-a7ca-0754d25fc408
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","delivery_channel":"side_chat","delivery_target_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Board unblock watch. Run `python3 ~/workspace/board-build/unblock_watch.py` — it prints a JSON list of board tasks that newly became actionable (blockers cleared or start date reached) and were never handled before.

For each task in the list:
- If the work is yours to do (drafting, research, building, configuring): do it now, then report the result briefly in this chat.
- If the step is BalRam's (his account, his approval, something only he can do): send him one concise message naming the task, why it is now unblocked, and exactly what his step is.
- After handling a task (work done or BalRam notified), append its id to the "handled" array in ~/workspace/board-build/hidden_files/unblock_watch_state.json so it never fires twice. Read-modify-write carefully to preserve existing entries.

Rules:
- Only act on tasks in the script's output. Never start other tasks.
- Empty output: stay silent, send nothing.
- Never edit task statuses directly in tasks.json; status changes go through the board flow (push_board.py).
- This run should land inside 8 AM–11 PM America/Toronto; if one ever lands outside that window, do the autonomous work but hold BalRam's notifications for the next run (leave those ids unmarked).
