---
id: task-due-date-watch
title: Task due date watch
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
  time: 08:42:00
  timezone: America/Toronto
delivery:
- chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: daily@08:42:00
path: /home/hatch/workspace/goals/all-threads-status-board-upkeep/crons/daily/task-due-date-watch__daily@08:42:00.md
is_heartbeat: false
is_system: false
---
Check BalRam's goal tasks for due dates that are approaching or overdue.

1. List all goals via the user_goal tools and pull each goal's tasks with due dates.
2. Identify tasks due within the next 48 hours and tasks already overdue.
3. For each, note the goal, task title, due date, and status.

Report: one concise message to the Main chat listing upcoming (due ≤ 48h) and overdue tasks, grouped by goal. If none are upcoming or overdue, stay silent.

This job never modifies tasks or goals — read-only except for its own log entry to the daily notes file (~/memory/YYYY-MM-DD.md).
