---
id: task-due-date-watch
title: Task due-date watch
enabled: true
owner: goal:all-threads-status-board-upkeep
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 08:42:00
delivery:
  - surface: side_chat
    to: 9c6459ad-00f6-47e3-a7ca-0754d25fc408
metadata:
  tags: [cron:flexible-time]
  originating_channel_context_json: '{"originating_channel":"side_chat","chat_kind":"direct","conversation_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","delivery_channel":"side_chat","delivery_target_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Daily task due-date watch for the All Threads Status Board (repo: technology-consults/cross-thread-task-status-tracker, live at https://technology-consults.github.io/cross-thread-task-status-tracker/).

Do all work through this Python flow (GitHub is API-only — never use a browser for GitHub):

1. Run a Python script that:
   a. GETs /repos/technology-consults/cross-thread-task-status-tracker/contents/tasks.json via `python3 ~/workspace/skills/github/bin/gh_api.py` (it prints response JSON; parse it in Python via subprocess). Base64-decode the `content` field to get the dataset; keep the `sha`.
   b. Sets today = current date in America/Toronto as YYYY-MM-DD (the user's timezone — use the real current date, NOT meta.asOf).
   c. For every task whose status is not "agreed" and not "rejected" and which has a due date, computes days = (due - today) in whole days and buckets it: OVERDUE (days < 0), DUE TODAY (days == 0), DUE WITHIN 2 DAYS (1–2), DUE THIS WEEK (3–7).
   d. Prints the flagged tasks grouped by thread: one line per task as `task-id | title | due YYYY-MM-DD | BUCKET`.
   e. Sets meta.asOf to today's date (leave meta.lastUpdated untouched — it records when task data last changed, not the daily refresh). If asOf already equals today, skip the push. Otherwise PUTs the updated file back to /repos/technology-consults/cross-thread-task-status-tracker/contents/tasks.json with the sha from step (a) and commit message `Daily board date refresh: asOf YYYY-MM-DD`.

2. For each thread with at least one flagged task, send ONE chat.send_message to that thread's task-tracker chat, addressed to that chat's agent, asking it to post the alert to the user in that chat. Tracker chat IDs:
   - Short Video: d82796e3-56f1-4d34-bf51-665165a38e92
   - Trading: 1ff0cb94-8438-4900-8c47-a39846cbf1a3
   - Vehicle: 547fb3d1-6b69-4410-b9d0-084cd478e7ff
   Keep each alert compact: one line per task — task id, title, due date, bucket. Threads with nothing flagged get no message.

3. If anything was posted to a tracker or the asOf push failed, append one line to today's daily log at ~/memory/YYYY-MM-DD.md. Do not edit MEMORY.md.

Stay quiet on uneventful days: if nothing was flagged and the asOf refresh succeeded, your final message should simply say the watch ran, zero tasks flagged, asOf refreshed to today's date — routine, nothing for the user to see.
