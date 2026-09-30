# cross-thread-task-status-tracker

The main repo for everything that touches all projects or lives across Muse
threads: the All Threads Status Board, the board/watcher machinery, the
versioned cron-definition mirror, the shared NYSE holiday list, and the
cross-cutting automation scripts.

Created 2026-09-27 · Last updated 2026-09-29

## What's here

| Path | What it is |
|---|---|
| `index.html`, `board.css`, `tasks.json` | The All Threads Status Board (served via GitHub Pages) |
| `scripts/push_board.py` | Publishes board updates (validates + commits via the GitHub API) |
| `scripts/unblock_watch.py` | Watches for cleared task blockers per project thread |
| `scripts/pending_digest.py` | Builds the per-thread task digests (action-needed + in-flight) |
| `scripts/sync_crons_to_git.py` | Mirrors every saved cron definition into `crons/` (one-way; scheduler is source of truth) |
| `scripts/pull_all_repos.sh` | Pulls all project repos to their latest state |
| `scripts/sync_holiday_copies.py` | Validates the NYSE holiday JSON and mirrors it one-way to `holidays/nyse_holidays.json` |
| `crons/` | Versioned mirror of every saved cron definition |
| `holidays/nyse_holidays.json` | The shared NYSE full-day closure list (rolling next four months) |
| `docs/technical/scheduled-jobs.md` | The current list of every scheduled job |
| `docs/workspace-directory-guide.md` | Plain-words map of the agent's workspace |
| `artifacts/` | Thin copies of user-facing artifacts (Artifact Index) |

## Conventions

- GitHub operations are API-only — never browser, never CLI push.
- Routine automated pushes (board data, cron mirrors, holiday mirrors,
  price bundles) are not tagged. Tags mark code releases only.
- Cron bodies may embed their working logic; the `crons/` mirror here is a
  read-only copy — the scheduler is the source of truth.
