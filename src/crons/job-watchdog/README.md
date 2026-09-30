# job-watchdog

*Job package for the versioned-cron architecture. Created: 2026-09-30 · Last modified: 2026-09-30*

Daily (06:00 America/Toronto) health check over the fixed watch list of 15
recurring scheduled jobs. Reports ONLY problems; the all-healthy line is
exactly `Watchdog: all scheduled jobs healthy.` Detection and reporting only —
never fixes anything, never modifies a schedule, never self-checks.

## Layout

| File | What it is |
|---|---|
| `run.py` | Package entrypoint: fixed rules + agent handshake + report |
| `github_api.py` | Minimal contents-API helper (vendored per job; api.github.com only) |
| `tests/test_watchdog.py` | Unit + handshake tests |

## Track B: script-as-orchestrator

- **Script-driven:** the complete watch list (fixed; never extended), the
  missed-run windows, the etf-live-bundle active-hours rule (weekdays
  04:00–21:00 ET → 30 min, else 3 days), the NYSE non-trading-day extension
  (ETF jobs 1–4, 6, 8, 12 → 3 days on weekends/market holidays), the
  disabled-job skip, and the latest-failed / missed-run decision rules.
- **Agent-driven (handshake):** `cron.status` (enabled?) and `cron.runs`
  (recent runs: time, status, error text) per watched job. The script cannot
  call these tools; the agent is the callable service for that step.

Handshake: script exits 10 with `@@AGENT-REQUEST-BEGIN@@` JSON
`{need, task, schema, attempt}`; the agent returns
`{jobs: [{id, enabled, runs: [{at, status, error}]}]}`. Schema-validated,
max 5 rounds, then exit 20 (fail loudly, never partial).

## Runtime data (not code)

- `holidays/nyse_holidays.json` in this repo (via API) for the trading-day
  check; falls back to weekend-only logic with a note if unavailable.
- `CRON_JOB_STATE_DIR` env, else `<home>/.cron_runner/job_state/job-watchdog/`.
- Problems are appended to `<home>/memory/YYYY-MM-DD.md` (daily log).

## Reply contract

- All healthy: exactly `Watchdog: all scheduled jobs healthy.`
- Problems: one line per problem — job id, last run time, status, error
  text, plus transient vs needs-attention verdict.
