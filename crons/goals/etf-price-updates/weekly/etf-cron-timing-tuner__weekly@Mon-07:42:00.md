---
id: etf-cron-timing-tuner
title: ETF alert timing tuner (4-week self-tune)
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  kind: weekly
  timezone: America/Toronto
  time: 07:42:00
  dow: [Mon]
delivery:
  - chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"3c672068-efb2-446c-9e50-aa0a3d02adf1","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Weekly timing tuner for the ETF price alert crons. Purpose: keep alert delivery times close to the agreed slots by adjusting each alert job's fire lead (how many minutes before its slot it fires) based on measured data-prep times. You run weekly on Mondays for 4 weeks (Oct 5 – Oct 26, 2026), then go dormant.

DORMANCY CHECK FIRST: get today's date in America/Toronto. If today is after 2026-10-26:
1. Disable yourself: cron.update(id="etf-cron-timing-tuner", enabled=false).
2. Post one final summary to the chat: the final lead times in effect for etf-price-updates and etf-price-preclose, and the average prep times measured over the 4 weeks.
3. End. You will never run again.

Otherwise, tune as follows:

1. Read the timing log at ~/workspace/goals/etf-price-updates/hidden_files/cron_timing_log.json (create it as [] if missing). Each entry: {"date": "YYYY-MM-DD", "job": "etf-price-updates"|"etf-price-preclose", "old_lead_min": N, "new_lead_min": M}. The lead in effect on any date = new_lead_min of the latest entry for that job with date <= that date. Defaults: 30 for dates before 2026-09-28, 15 for 2026-09-28 onward.

2. Measure recent prep times. In ~/workspace/goals/etf-price-updates/hidden_files/, take widget input files named etf_widget_input_*.json from the last 14 days (e.g. etf_widget_input_2026-10-05_1200.json; preclose ones contain "_preclose"). Skip slots that produced no file (silent runs). For each file:
   - Parse the slot: the HHMM in the filename is the alert slot (1200 → 12:00); the date prefix is the trading date. Combine into a slot datetime in America/Toronto.
   - Parse the asof timestamp: the input JSON's "asof" field looks like "Mon Oct 5 · ~12:33 PM ET · Market open" — the "~h:MM AM/PM" is when quotes were fetched (prep finished). Convert to a datetime on the file's date.
   - fire = slot datetime − lead_in_effect(slot date) minutes from step 1 (preclose slot is 15:30).
   - prep_minutes = (asof − fire). Keep values with 0 < prep < 60 (drop negatives and outliers).
   - Attribute: filename contains "preclose" → etf-price-preclose, else etf-price-updates.

3. For each job with 3 or more kept samples: avg = mean prep. Suggested lead = round((avg + 5) / 5) * 5, clamped to [10, 25] minutes.

4. Get each job's current lead: cron.view the job and compare its fire times to the slot mapping (slots 08:00, 10:00, 12:00, 14:00, 18:00, 20:00 for etf-price-updates; 15:30 for etf-price-preclose). Current lead = slot − fire.

5. If |suggested − current| >= 5 for a job, update it via cron.update:
   - etf-price-updates (interval 2h): new fire times = each slot − suggested minutes. Set schedule at = the next upcoming fire datetime (e.g. suggested=20 → fires at :40 → at = the next 07:40/09:40/… occurrence from now), every=2h, timezone America/Toronto. In the body: replace the lead sentence ("fires about N minutes before each alert slot") with the new N and refresh the measured-average note with the new avg and date range; rewrite the fire→slot mapping lines (e.g. "07:40 → 08:00 slot, 09:40 → 10:00, 11:40 → 12:00, 13:40 → 14:00, 17:40 → 18:00, 19:40 → 20:00") and the silent line (e.g. "15:40 and any other time → stay silent"); update the rounding-grid note to match the new fire minutes.
   - etf-price-preclose (daily): new time = 15:30 − suggested minutes (HH:MM:00), timezone America/Toronto. Update the body's lead sentence the same way.
   - Append {"date": today, "job": ..., "old_lead_min": current, "new_lead_min": suggested} to cron_timing_log.json.
   - Verify with cron.view/cron.status that the new schedule saved, and confirm the reported next run.
   - Report the change to the chat (visible): old lead → new lead, measured avg prep, next run time.
   - If the cron tools are unavailable in your context, do NOT silently skip: report the recommended new fire times and leads in your handoff instead.

6. If no job needs a change (|diff| < 5 for both, or fewer than 3 samples for a job): stay silent — no chat message. Still append a brief measurement note to the daily memory log (~/memory/YYYY-MM-DD.md): date, samples per job, avg prep, lead unchanged.

7. Never change anything else: alert slots, widget formats, delivery chats, and the alert bodies' substance stay as-is. Never touch etf-signal-intraday or any other job.
