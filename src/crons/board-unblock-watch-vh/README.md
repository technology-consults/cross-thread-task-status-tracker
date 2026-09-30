# board-unblock-watch-vh

*Job package for the versioned-cron architecture. Created: 2026-09-30 · Last modified: 2026-09-30*

Hourly watch over the **Vehicle** thread's board tasks: newly-unblocked work
plus a sweep for idle todo / stalled in_progress / completed_stalled tasks.

## Layout

| File | What it is |
|---|---|
| `run.py` | Package entrypoint (THREAD=vh, tracker chat `547fb3d1-6b69-4410-b9d0-084cd478e7ff`) |
| `unblock_watch.py` | Vendored watcher (adapted: tasks.json via GitHub API, API state) |
| `github_api.py` | Minimal contents-API helper (vendored per job; api.github.com only) |
| `tests/` | Unit tests for the watcher and the entrypoint |

## Track B: script-as-orchestrator

- **Script-driven:** unblock detection and the sweep (deterministic rules),
  handled-id state (seeded once from the legacy workspace copy), digest.
- **Agent-driven (handshake):** per-task decisions and actions — review
  tasks + unblock notices for BalRam's steps, doing my own work, status
  marks. Sweep entries are report-only (never auto-acted).

Handshake: exit 10 with `@@AGENT-REQUEST-BEGIN@@` JSON; max 5 rounds, then
exit 20. Both lists empty → silent, exit 0, no agent call.

## Runtime data (not code)

- `tasks.json` from this repo via the GitHub API (never a local checkout).
- `CRON_JOB_STATE_DIR` env, else `<home>/.cron_runner/job_state/board-unblock-watch-vh/`.
