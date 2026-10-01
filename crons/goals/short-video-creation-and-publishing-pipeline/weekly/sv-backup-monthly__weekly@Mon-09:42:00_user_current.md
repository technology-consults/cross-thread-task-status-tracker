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
  originating_chat_context_json: '{"chat_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Monthly off-cloud backup of the short-video archive (program item 1.8, design 0.4 section 4.1).

This job fires every Monday morning but only ACTS on the first Monday of the month (the cron scheduler cannot express "first Monday" directly). If today is not the first Monday of the month, do nothing and report "skipped — not the first Monday".

On the first Monday:
1. Run the backup FROM GIT (code from git, outputs to their usual durable dirs — BalRam's standing rule 2026-09-30; never run ~/workspace/short-video/build/ directly):
   cd ~/workspace/repos/short-video && python3 scripts/run_from_git.py --env staging -- python3 build/backup/backup_job.py --env prod
   (the --env staging before the -- selects the git execution environment; the --env prod after it is the backup job's own config selector — which archive_root to back up)
   (source of truth: technology-consults/short-video, build/backup/backup_job.py)
2. The script rebuilds `short-video-archive-backup.zip` (round-trip verified), places the off-cloud copy where BalRam can download it, and prints a "Download nudge:" line naming the ZIP, its size, how many videos it covers, and the newest video date.
3. Put that nudge line in your final message — it is BalRam's monthly reminder to download the ZIP to his own computer (the copy that survives even a total cloud loss).

Rules: never write to MEMORY.md (observations go to ~/memory/YYYY-MM-DD.md). If the backup fails, report the failure plainly with the exact error — do not retry blindly. This job never publishes anything and never touches platform APIs.
