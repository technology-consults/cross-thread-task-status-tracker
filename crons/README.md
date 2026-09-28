# Cron definitions

Versioned mirror of every saved cron definition (the scheduler's read-only
copies). The scheduler is the source of truth — this directory never feeds
back into it.

Layout mirrors the workspace sources:

- `shared/` — copies from `~/workspace/cron.d/` (hourly, daily, … plus
  `_archive/` for retired definitions)
- `goals/<goal-slug>/` — copies from `~/workspace/goals/<goal-slug>/crons/`
  (goal-owned schedules)

Kept current by `scripts/sync_crons_to_git.py`, run daily by the
`cron-definitions-sync` cron. It commits only when something changed.
