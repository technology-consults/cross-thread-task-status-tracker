---
id: sv-gate-exception-pokes
title: 'Hourly poke: gate-exception approvals (prod-critical)'
enabled: true
owner: goal:short-video-creation-and-publishing-pipeline
mode: task
schedule:
  kind: interval
  timezone: America/Toronto
  at: 2026-09-30T09:27:23
  every: 1h
delivery:
  - chat_id: b95fb15f-a58f-4547-b9cd-cdce882a5cd9
metadata:
  tags: [cron:automatic-interval-anchor]
  originating_chat_context_json: '{"chat_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Hourly gate-exception poke check (prod-critical). Silent unless there is work.

1. Fetch the live board: GET https://api.github.com/repos/technology-consults/cross-thread-task-status-tracker/contents/tasks.json with header `Accept: application/vnd.github.raw`, authenticating via the stored custom.github credential using the dynamic_credentials surrogate (`sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")`, `add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])`). Never print the credential.
2. Parse the JSON. Find tasks where `status == "pending_review"`, `assigned_to == "BalRam"`, and `poke == "hourly"`.
3. If none: stay completely silent — no user-visible message.
4. If any: this is a prod-critical gate exception awaiting his approval. There is NO 3-poke cap on these (his explicit override for prod-critical exceptions — keep poking hourly until resolved). Send one short poke per open task to the delivery chat: the task title, what exception is being asked for, and that it is blocking prod-critical work. One or two lines each, plain words.
