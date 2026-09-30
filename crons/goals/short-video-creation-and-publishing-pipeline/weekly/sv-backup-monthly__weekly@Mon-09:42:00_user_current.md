---
id: sv-backup-monthly
title: Monthly off-cloud video archive backup
enabled: true
owner: goal:short-video-creation-and-publishing-pipeline
mode: task
schedule:
  kind: weekly
  timezone: '@user.current'
  time: 09:42:00
  dow: [Mon]
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false}'
  presentation_locale: en-US
---
Monthly off-cloud backup of the short-video archive (program item 1.8, design 0.4 section 4.1).

This job fires every Monday morning but only ACTS on the first Monday of the month (the cron scheduler cannot express "first Monday" directly). If today is not the first Monday of the month, do nothing and report "skipped — not the first Monday".

On the first Monday:
1. Run: `python3 ~/workspace/short-video/build/backup/backup_job.py --env prod`
   (source of truth: technology-consults/short-video, build/backup/backup_job.py)
2. The script rebuilds `short-video-archive-backup.zip` (round-trip verified), places the off-cloud copy where BalRam can download it, and prints a "Download nudge:" line naming the ZIP, its size, how many videos it covers, and the newest video date.
3. Put that nudge line in your final message — it is BalRam's monthly reminder to download the ZIP to his own computer (the copy that survives even a total cloud loss).

Rules: never write to MEMORY.md (observations go to ~/memory/YYYY-MM-DD.md). If the backup fails, report the failure plainly with the exact error — do not retry blindly. This job never publishes anything and never touches platform APIs.
