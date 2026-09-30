# holiday-list-update

*Job package for the versioned-cron architecture. Created: 2026-09-30 · Last modified: 2026-09-30*

Quarterly (1st of Jan/Apr/Jul/Oct, 20:00 America/Toronto) NYSE/Nasdaq holiday
calendar refresh. This job is the ONLY writer of the shared holiday list.

## Layout

| File | What it is |
|---|---|
| `run.py` | Package entrypoint: window math → agent handshake → validate → write → mirror |
| `sync_holiday_copies.py` | Vendored from `scripts/sync_holiday_copies.py` (2026-09-30); default-path only |
| `tests/test_holiday.py` | Unit + handshake tests |

## Track B: script-as-orchestrator

- **Script-driven:** window computation (next four calendar months from the
  current month), result validation (real YYYY-MM-DD dates, inside the
  window), canonical-JSON construction, local write, and the vendored
  mirror sync (GitHub API; never touches the trading portal).
- **Agent-driven (handshake):** fetching the two press-release calendars and
  extracting full-day closures — live web research with source-substitution
  judgment (if the Nasdaq copy doesn't cover the window, find the current
  Nasdaq publication that does). The script cannot do this; the agent is the
  callable service for that step.

Handshake: script exits 10 with `@@AGENT-REQUEST-BEGIN@@` JSON
`{need, task, schema, attempt}`; the agent returns
`{holidays, nyse_url, nasdaq_url, disagreement}`. Schema-validated, max 5
rounds, then exit 20 (fail loudly, never partial).

Cross-check rule (from the definition, enforced in code): on source
disagreement the job writes NOTHING and reports the disagreement instead.

## Runtime data (not code)

- `CRON_HOLIDAYS_JSON` env, else `<home>/workspace/shared/holidays/nyse_holidays.json`
  — the authoritative local copy (written by this job, read by everything else).
- `CRON_JOB_STATE_DIR` env, else `<home>/.cron_runner/job_state/holiday-list-update/`.

## Reply contract

- Success: silent one-liner (no user message per the definition).
- Disagreement / bad dates / sync failure: brief flag message, exit 0
  (defined outcomes the thin body delivers to the job's chat target).
- Fetch/validation of the agent result failing after 5 rounds: loud, exit 20.
