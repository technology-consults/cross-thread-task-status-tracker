---
id: precon-digest
title: Precon builder email digest
enabled: false
owner: goal:builder-email-digest
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 08:42:00
delivery: []
metadata:
  tags: [cron:flexible-time]
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Precon builder-email digest — READ-ONLY.

Each morning, check the Gmail Precon label for new builder/preconstruction emails and post a short chat digest only if something new arrived. Never touch the inbox.

State file: workspace/.jarvis/idea-executions/a21eb261-dff3-452c-b426-be6e1ba1c9a9/scratch/precon_digest_state.json
Format: {"seen_ids": ["<gmail message id>", ...], "last_digest_time": "<ISO-8601 timestamp of when the last digest ran, e.g. 2026-09-22T08:42:00-04:00>", "last_new_mail_date": "YYYY-MM-DD", "quiet_days": <int>}. The Precon label id is Label_1.

Steps:
1. Read the state file. If it is missing, treat all currently listed mail as already seen (baseline it, report nothing), set last_digest_time to now, and write the state file.
2. The digest covers the window from last_digest_time up to now. Derive the date of last_digest_time as YYYY/MM/DD and list messages under the Precon label received since then, paginating through all pages:
   hatch_gws_cli gmail users messages list --params '{"userId":"me","labelIds":["Label_1"],"maxResults":500,"q":"after:YYYY/MM/DD"}'
   (replace YYYY/MM/DD with the last digest's date). Follow nextPageToken until there are no more pages. This windowed query plus the seen_ids check below guarantees every email received between the last digest prep and now is reviewed.
3. New arrivals = ids in that listing not present in seen_ids.
4. If new arrivals exist, read each with:
   hatch_gws_cli gmail users messages get --params '{"userId":"me","id":"<id>","format":"full"}'
   Then compose ONE short digest as this run's chat message: ONLY include emails that mention a price or price range for the project (e.g. "from $X", "$X–$Y", "starting in the $500s"). Skip any email with no pricing information at all. For each included email give the builder/sender name, the project, the prices, and key dates. Quote email content only minimally — just what the summary needs. Keep it short, a few lines per email, no headers, no fluff. If new emails arrived but none of them have any pricing, stay silent that day (no digest).
5. Update the state file: add ALL new ids to seen_ids (including ones skipped for lack of pricing, so they are never reported later), set last_digest_time to the current run's timestamp, set last_new_mail_date to today's date in America/Toronto, reset quiet_days to 0. If there was nothing new, increment quiet_days by 1 and leave the rest unchanged.
6. If quiet_days reaches 30 (a full month with no new builder mail): post one final chat message saying no new builder mail has arrived in a month so the digest is pausing itself, then remove this schedule with cron.remove using id precon-digest.

Hard rules — never break these:
- Read-only, always: never create, edit, or delete Gmail filters, labels, or settings.
- Never mark any message read or unread; never archive, move, or delete anything.
- Only ever read mail under the Precon label (Label_1). Do not scan the rest of the inbox for any reason.
- At most one digest per day; stay completely silent on days with nothing new.
