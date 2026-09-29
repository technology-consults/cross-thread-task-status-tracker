# Scheduled Jobs

**Created:** 2026-09-28 12:18 EDT · **Last modified:** 2026-09-29 09:00 EDT

Every scheduled job (cron) currently saved, compiled from the live scheduler on 2026-09-29. Regular cron tasks are not board items — only status-change flow items go on the board (rule confirmed 2026-09-28).

## Running now

| Job | Schedule | What it does | Delivers to |
|---|---|---|---|
| board-unblock-watch-sv | Every hour | Watches the Short Video board for tasks whose blockers just cleared; starts the agent's, pokes you for yours | Short Video — task tracker |
| board-unblock-watch-tr | Every hour | Same for the Trading board | Trading — task tracker |
| board-unblock-watch-vh | Every hour | Same for the Vehicle board | Vehicle — task tracker |
| etf-live-bundle | Every 5 min (weekdays 04:00–21:00 ET) | Bakes fresh market data into the live ETF page | Silent — updates the page itself |
| etf-price-updates | Every 2 hours | QQQ/SPY/GLD price cards with 1-month and 3-month charts | Trading |
| etf-signal-intraday-market | Every hour (04:00–20:00 ET) | Market-hours signal watch; silent unless a strong signal fires | Trading |
| etf-signal-intraday-offhours | Every 6 hours | Off-hours signal watch (nights, weekends, holidays); silent unless a strong signal fires | Trading |
| repo-pull-hourly | Every hour | Pulls the project repos to their latest GitHub state | Silent |
| etf-price-preclose | Daily 15:15 ET | Pre-close price snapshot | Trading |
| etf-trading-signals | Daily 07:30 ET | Morning BUY/SELL/HOLD signal report with targets | Trading |
| signal-scorecard | Daily 08:42 ET | Grades published signals against their targets; posts only when something changed | Trading |
| etf-signal-engine-review | Fridays 17:42 ET | Weekly engine health check; reports only on "attention" | Trading |
| etf-cron-timing-tuner | Mondays 07:42 ET | Tunes cron lead times from measured run durations | Internal |
| phev-ev-suv-deal-watch | Daily 08:00 ET | Ontario EV SUV deal scan (sub-3% rate, $150–$200 bi-weekly) | Vehicle |
| phev-ev-suv-payment-watch | Daily 08:42 ET | Payment-only scan for the SUV goal | Vehicle |
| task-due-date-watch | Daily 08:42 ET | Flags board tasks due soon or overdue; stays quiet when nothing is flagged | The three task trackers |
| cron-definitions-sync | Daily 06:42 ET | Mirrors every cron definition into this repo's `crons/` | Silent — commits to git |
| portal-links-watch | Daily 07:42 ET | Re-verifies every portal URL live; posts only when something changed | Portal links chat |
| regression-watchdog | Daily 07:42 ET | Regression watchdog | Main chat |
| holiday-list-update | 1st of Jan/Apr/Jul/Oct, 20:00 ET | Refreshes the NYSE holiday list (next four calendar months) | Silent unless sources disagree |
| job-watchdog | Every hour | Checks the last runs of all scheduled jobs; reports only problems | Main chat |
| heartbeat | Every 30 min | Internal heartbeat checklist | Internal |
| failure-log-weekly | Saturdays 09:42 ET | Weekly failure-trend accountability check (your request, 2026-09-26) | EVs & PHEVs |

Notes:
- The old `etf-signal-intraday` (every 2h from 09:30 ET) was decommissioned
  2026-09-29 and replaced by the market-hours and off-hours watches above.
- The old weekly `holiday-list-update` was replaced 2026-09-29 by the
  quarterly schedule above.

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

Old schedule definitions kept under `crons/shared/_archive/` — no longer active: agentic-feature-tour, backtest-report-delivery, board-unblock-watch (older 12-hourly/1-hourly), etf-price-preclose (older), etf-price-updates (older 2-hourly), etf-signal-intraday (decommissioned 2026-09-29), holiday-list-update (older weekly), job-watchdog (older), precon-digest (older), strategy-research-updates, tiktok-validation-retry (canceled 2026-09-27).

---

*End of list. Recompiled from the live scheduler — ask for a refresh anytime jobs change.*
