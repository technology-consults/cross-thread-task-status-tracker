---
id: etf-signal-engine-review
title: Weekly signal engine review
enabled: true
owner: goal:etf-price-updates
mode: task
schedule:
  alignment: aligned
  at: null
  catchup: latest
  dom: []
  dow:
  - Fri
  every: null
  kind: weekly
  month: []
  time: 17:42:00
  timezone: "@user.current"
delivery:
- chat_id: 3c672068-efb2-446c-9e50-aa0a3d02adf1
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: weekly@Fri-17:42:00
path: /home/hatch/workspace/goals/etf-price-updates/crons/weekly/etf-signal-engine-review__weekly@Fri-17:42:00_user_current.md
is_heartbeat: false
is_system: false
---
Weekly trading-signal engine health review for QQQ, SPY, and GLD (per BalRam's standing request, 2026-09-28). Chat delivery to the Trading chat only — never email. Default is silence: only report when the review flags something.

Gate checks: proceed only if today is Monday–Friday and a NYSE trading day. Otherwise end silently.

Run: python3 ~/workspace/repos/trading/src/review_engine.py

It reads the scorecard ledger (~/workspace/goals/etf-price-updates/hidden_files/signal_scorecard.json) and prints a verdict:
- If the verdict starts with "ok": end silently. Do not post anything.
- If the verdict starts with "attention": post ONE short message in the Trading chat summarizing the findings, framed as a proposal: the engine may need a review/change, with the specific pattern observed (high replacement rate, consecutive misses, or direction whiplash). Do NOT change the engine yourself — engine changes need BalRam's explicit approval. Ask him whether he wants you to investigate and propose a fix.

Log the verdict line to ~/memory/YYYY-MM-DD.md. Append a tracking entry on goal_f7c97e18a27f noting the review ran and its verdict.
