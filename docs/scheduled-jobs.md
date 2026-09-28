# Scheduled Jobs

**Created:** 2026-09-28 12:18 EDT · **Last modified:** 2026-09-28 12:18 EDT

Every scheduled job (cron) currently saved, compiled from the live scheduler on 2026-09-28. Regular cron tasks are not board items — only status-change flow items go on the board (rule confirmed 2026-09-28).

## Running now

| Job | Schedule | What it does | Delivers to |
|---|---|---|---|
| board-unblock-watch-sv | Every hour | Watches the Short Video board for tasks whose blockers just cleared; starts the agent's, pokes you for yours | Short Video — task tracker |
| board-unblock-watch-tr | Every hour | Same for the Trading board | Trading — task tracker |
| board-unblock-watch-vh | Every hour | Same for the Vehicle board | Vehicle — task tracker |
| etf-live-bundle | Every 5 min (weekdays 04:00–21:00 ET) | Bakes fresh market data into the live ETF page | Silent — updates the page itself |
| etf-price-updates | Every 2 hours | QQQ/SPY/GLD price cards with 1-month and 3-month charts | Trading |
| etf-price-preclose | Daily 15:00 ET | Pre-close price snapshot | Trading |
| etf-trading-signals | Daily 07:30 ET | Morning BUY/SELL/HOLD signal report with targets | Trading |
| etf-signal-intraday | Every 2 hours from 09:30 ET | Watches for strong signal changes; silent unless one fires | Trading |
| signal-scorecard | Daily 08:42 ET | Grades published signals against their targets; posts only when something changed | Trading |
| etf-signal-engine-review | Fridays 17:42 ET | Weekly engine health check; reports only on "attention" | Trading |
| phev-ev-suv-deal-watch | Daily 08:00 ET | Ontario PHEV/EV SUV deal scan (sub-3% rate, $150–$200 bi-weekly) | EVs & PHEVs |
| phev-ev-suv-payment-watch | Daily 08:42 ET | Payment-only scan for the SUV goal | EVs & PHEVs |
| task-due-date-watch | Daily 08:42 ET | Flags board tasks due soon or overdue; stays quiet when nothing is flagged | The three task trackers |
| job-watchdog | Every hour | Checks the last runs of all scheduled jobs; reports only problems | Main chat |
| heartbeat | Every 30 min | Internal heartbeat checklist | Internal |
| failure-log-weekly | Saturdays 09:42 ET | Weekly failure-trend accountability check (your request, 2026-09-26) | EVs & PHEVs |

## Disabled

| Job | Schedule | What it does | Notes |
|---|---|---|---|
| precon-digest | Daily 08:42 ET | Builder email digest | Off since 2026-09-26 at your request; stays off until you ask to reactivate |

## One-time, already fired

| Job | Ran | What it did |
|---|---|---|
| publish-build-summary-8am | 2026-09-28 08:00 ET | Presented the publish-build summary in the Short AI videos project chat |

## System jobs (runtime-managed, not yours to change)

| Job | Schedule | What it does |
|---|---|---|
| deterministic-doctor | Every hour | Runtime health check |
| feed-pulse-00 … feed-pulse-23 | Hourly, one per hour | Builds your Feed (personal newspaper) content for that hour |
| profile-image | Weekly | Profile image refresh |

## Retired definitions

Old schedule definitions kept under `cron.d/_archive/` — no longer active: agentic-feature-tour, backtest-report-delivery, board-unblock-watch (older 12-hourly/1-hourly), etf-price-preclose (older), etf-price-updates (older 2-hourly), job-watchdog (older), precon-digest (older), strategy-research-updates, tiktok-validation-retry (canceled 2026-09-27).

---

*End of list. Recompiled from the live scheduler — ask for a refresh anytime jobs change.*
