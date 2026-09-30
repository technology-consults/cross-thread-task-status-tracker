---
id: sv-chat-review
title: All-chats review → docs/git/board (capture only)
enabled: true
owner: goal:all-threads-status-board-upkeep
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 10:42:00
timeout_secs: 7200
delivery:
  - chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Daily sweep of every Hatch chat (Main + side chats). Purpose: nothing agreed, proposed, decided, or left pending in a chat may die in that chat. Extract it into the durable record. Created per his 2026-09-29 instruction. THIS JOB IS CAPTURE-ONLY — it never nudges BalRam. The single poke stream is the `sv-balram-pokes` cron (platform items only, "For review" thread only, max 3 nudges per item); this job feeds it, never duplicates it.

BalRam's standing autonomy rule (2026-09-29): stop and wait for him ONLY on items that build, ship, and hit the platforms. Everything else — jobs, scripts, code, docs, design decisions — Muse decides the best option and proceeds, building it reversible. No reviews from him on those.

STATE FILE: ~/workspace/goals/all-threads-status-board-upkeep/hidden_files/chat_review_state.json — keeps per-chat message watermarks (so each run reads only new messages). Read it first; write it back at the end.

WORK:
1. List all chats (chat.list), then read new messages in each since its watermark (chat.read_messages). Skip system/heartbeat noise; focus on user↔assistant exchanges.
2. For each new message, extract: proposals, concerns, agreements, decisions, gates, strategies, pending items, tasks assigned to BalRam, review tasks awaiting his written word. Skip anything already captured elsewhere.
3. File durable items in the correct place: project docs under ~/workspace/<project>/ (then commit the doc change through the GitHub API to the matching repo — GitHub is API-only, never the browser; local clones cannot push, so use the API then re-sync the clone), the All Threads Status Board repo (cross-thread-task-status-tracker) for cross-thread tasks, program.json for program items. Never leave a decision/proposal/gate only in chat.
4. FEED THE POKE STREAM: if an extracted item is short-video work that builds/ships/hits the platforms and needs BalRam (a release, go-live, production deploy, or an approval he owes on one), make sure it is recorded in program.json with a `due` date and assigned to him — the poke cron reads that and surfaces it. Never invent a due date — only file dates he actually set or that were agreed in the chat.
5. AUTONOMOUS ITEMS: if an extracted item is a job, script, code, doc, or design decision that does NOT hit the platforms, decide the best option yourself and proceed — implement it, record the decision in the relevant doc/decision file and in ~/memory/YYYY-MM-DD.md, keep it reversible. Do not create review tasks for him on these.
6. TASKS DIGEST → TASK TRACKER (BalRam 2026-09-29): every captured task is filed as a task in the tracker's tasks.json (thread, title, status from the STATUS map, due when dated, detail, where = originating chat + date, assigned_to). The tasks digest lives in the tracker — it is NOT repeated in the chat message. Use push_board.py to publish the board after changes (it runs the regression suite itself; never deploy on a failing regression).
7. Your final message (this run's delivery target) covers ONLY the important discussions: proposals, decisions, agreements, gates, strategies, concerns — one line each with originating chat + date + where it now lives. If nothing new, one line saying so. No task lines here; tasks live in the tracker.

RULES: Do not invent facts or decisions — extract only what the messages actually say. A reaction is NEVER approval — never treat one as a decision. Task statuses must come from the board's STATUS map — never invent one. Do not edit ~/MEMORY.md directly; observations go to ~/memory/YYYY-MM-DD.md. Git writes follow the standing rule: API-only, workspace stays the working copy, tested-and-ready code also lands in git.
