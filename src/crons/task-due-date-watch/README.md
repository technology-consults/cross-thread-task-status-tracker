# task-due-date-watch

*Job package for the versioned-cron architecture. Created: 2026-09-30 · Last modified: 2026-09-30*

Daily (08:42 user-timezone) due-date watch for the All Threads Status Board.
Fetches `tasks.json` from `technology-consults/cross-thread-task-status-tracker`
via the GitHub API (never the browser), buckets tasks by days-until-due, and
refreshes `meta.asOf` to today's Toronto date.

## Layout

| File | What it is |
|---|---|
| `run.py` | Package entrypoint: fetch → bucket → asOf refresh → agent handshake → log |
| `github_api.py` | Minimal contents-API helper (vendored per job; api.github.com only) |
| `tests/test_watch.py` | Unit + handshake tests |

## Track B: script-as-orchestrator

- **Script-driven:** fetch tasks.json, bucketing (OVERDUE / DUE TODAY /
  DUE WITHIN 2 DAYS / DUE THIS WEEK), asOf refresh, result validation,
  daily-log append, round-state bookkeeping.
- **Agent-driven (handshake):** per-thread alert delivery — one chat message
  per flagged thread to that thread's task-tracker chat. The script cannot
  send chat messages; the agent is the callable service for that step.

Handshake: script exits 10 with `@@AGENT-REQUEST-BEGIN@@` JSON
`{need, task, schema, attempt}`; the agent posts the alerts and re-invokes
with `--agent-result '<json>'`. Schema-validated, max 5 rounds, then exit 20
(fail loudly, never partial).

## Runtime state (not code)

- `CRON_JOB_STATE_DIR` env, else `<home>/.cron_runner/job_state/task-due-date-watch/`
  — handshake round state (`round.json`), cleaned up when the round ends.
- Daily-log appends go to `<home>/memory/YYYY-MM-DD.md` (the job's defined
  output), only when something was posted or the asOf push failed.

## Reply contract

- Nothing flagged: `watch ran, zero tasks flagged, asOf ... — routine, nothing for the user to see.`
- Flagged: `watch ran, N thread(s) flagged, alerts posted to M chat(s).`
- Errors (fetch failure, invalid agent result after 5 rounds): brief text, non-zero exit.
