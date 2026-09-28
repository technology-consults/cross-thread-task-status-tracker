---
id: precon-digest
title: Precon builder email digest
enabled: true
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 08:42:00
delivery: []
metadata:
  tags: [cron:flexible-time]
  predicted_connector_permissions:
  - connector: gmail
    method: users.messages.get
  - connector: gmail
    method: users.messages.list
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Precon builder-email digest — READ-ONLY.

Each morning, check the Gmail Precon label for new builder/preconstruction emails and post a short chat digest only if something new arrived. Never touch the inbox.

State file: workspace/.jarvis/idea-executions/a21eb261-dff3-452c-b426-be6e1ba1c9a9/scratch/precon_digest_state.json
Format: {"seen_ids": ["<gmail message id>", ...], "last_new_mail_date": "YYYY-MM-DD", "quiet_days": <int>}. The Precon label id is Label_1.

Steps:
1. Read the state file. If it is missing, treat all currently listed mail as already seen (baseline it, report nothing) and write the state file.
2. List messages under the Precon label, paginating through all pages:
   hatch_gws_cli gmail users messages list --params '{"userId":"me","labelIds":["Label_1"],"maxResults":500}'
   Follow nextPageToken until there are no more pages.
3. New arrivals = ids not present in seen_ids.
4. If new arrivals exist, read each with:
   hatch_gws_cli gmail users messages get --params '{"userId":"me","id":"<id>","format":"full"}'
   Then compose ONE short digest as this run's chat message: for each new email give the builder/sender name, the project, any prices, and key dates. Quote email content only minimally — just what the summary needs. Keep it short, a few lines per email, no headers, no fluff.
5. Update the state file: add the new ids to seen_ids, set last_new_mail_date to today's date in America/Toronto, reset quiet_days to 0. If there was nothing new, increment quiet_days by 1 and leave the rest unchanged.
6. If quiet_days reaches 30 (a full month with no new builder mail): post one final chat message saying no new builder mail has arrived in a month so the digest is pausing itself, then remove this schedule with cron.remove using id precon-digest.

Hard rules — never break these:
- Read-only, always: never create, edit, or delete Gmail filters, labels, or settings.
- Never mark any message read or unread; never archive, move, or delete anything.
- Only ever read mail under the Precon label (Label_1). Do not scan the rest of the inbox for any reason.
- At most one digest per day; stay completely silent on days with nothing new.
