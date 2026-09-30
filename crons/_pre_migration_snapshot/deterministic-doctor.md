---
id: deterministic-doctor
title: Deterministic system doctor
enabled: true
owner: null
mode: task
schedule:
  alignment: aligned
  at: 2026-09-29T00:01:00
  catchup: latest
  dom: []
  dow: []
  every: 12h
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
schedule_key: interval@12h
path: /home/hatch/workspace/system-cron.d/deterministic-doctor.md
is_heartbeat: false
is_system: true
---
System health checker for the Muse runtime: verifies connectivity and core services on a regular cadence.
