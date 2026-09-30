---
id: profile-image
title: Profile image
enabled: true
owner: null
mode: task
schedule:
  alignment: aligned
  at: null
  catchup: latest
  dom: []
  dow: []
  every: 1w
  kind: interval
  month: []
  time: null
  timezone: America/Toronto
delivery: []
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: interval@1w
path: /home/hatch/workspace/system-cron.d/profile-image.md
is_heartbeat: false
is_system: true
---
Regenerates the user's profile image on a periodic basis.
