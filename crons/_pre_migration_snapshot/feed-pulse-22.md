---
id: feed-pulse-22
title: Feed pulse (slot 22)
enabled: true
owner: null
mode: task
schedule:
  alignment: aligned
  at: null
  catchup: latest
  dom: []
  dow: []
  every: 24h
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
schedule_key: interval@24h
path: /home/hatch/workspace/system-cron.d/feed-pulse-22.md
is_heartbeat: false
is_system: true
---
Write one short Feed item about the short-video program — what's new, what's changed, or what's worth knowing — so the user's Feed tab stays fresh. Use the same voice as the Feed's usual editorials. Skip weekends: if today is Saturday or Sunday, end the run silently with no post. Write the item to the Feed via the feed.create_unit tool.
