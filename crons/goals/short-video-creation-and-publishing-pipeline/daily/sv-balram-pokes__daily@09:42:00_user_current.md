---
id: sv-balram-pokes
title: 'Daily poke: BalRam''s due program tasks'
enabled: true
owner: goal:short-video-creation-and-publishing-pipeline
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 09:42:00
delivery:
  - chat_id: 1ea4c688-3d31-4f06-a369-180fd5e00405
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"1ea4c688-3d31-4f06-a369-180fd5e00405","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
BalRam's standing rule (2026-09-29): stop and wait for him ONLY on items that build, ship, and hit the platforms. Everything else — jobs, scripts, code, docs, design decisions — Muse decides the best option and proceeds, building it reversible (changeable/adjustable later). No reviews from him on those.

Run `python3 ~/workspace/goals/short-video-creation-and-publishing-pipeline/hidden_files/balram_poke.py` and read its output. Each line is an item assigned to BalRam, due within 3 days or overdue. Classify each:

1. PLATFORM ITEM (involves building/shipping/hitting a platform: public publish, go-live, production deploy, anything going live): this is a POKE. Send it directly to the "For review" thread via chat.send_message (chat id b95fb15f-a58f-4547-b9cd-cdce882a5cd9) — pokes only there, never status updates. One line per item, plain words: item, due date, what he needs to do. REMINDER CAP: read ~/workspace/goals/short-video-creation-and-publishing-pipeline/hidden_files/poke_counts.json (create if missing); each item gets at most 3 nudges total — nudge only below 3, increment and write back. Never proceed on a platform item without him.
2. NON-PLATFORM ITEM (jobs, scripts, code, docs, design decisions, internal tooling): do NOT poke. Decide the best option yourself and proceed — implement it, record the decision in the relevant doc/decision file and in ~/memory/YYYY-MM-DD.md, and keep it reversible (note how it can be changed later). Never mark his manual/decision steps done yourself, and never change a due date yourself.

Your final message (this run's delivery target, Main chat) is the status digest: one line per item you decided and acted on (what, where it landed, how it's reversible), plus one line per platform item poked. If the script printed nothing and nothing needed doing, stay silent — no message, no report.
