# cron-definitions-sync

*Job package for the versioned-cron architecture. Created: 2026-09-30 · Last modified: 2026-09-30*

Daily (06:42 America/Toronto) one-way mirror of the scheduler's saved cron
definitions into `crons/` in `technology-consults/cross-thread-task-status-tracker`,
plus the regenerated review page (`crons/index.html`, served by GitHub Pages).
Commits via the GitHub API as a single commit, only when something changed.

## Layout

| File | What it is |
|---|---|
| `run.py` | Package entrypoint: runs the vendored sync, prints the reply contract |
| `sync_crons_to_git.py` | Vendored from `scripts/sync_crons_to_git.py` (2026-09-30); see header for adaptations |
| `build_crons_page.py` | Vendored from `scripts/build_crons_page.py` (2026-09-30); docstring reworded only |
| `tests/test_sync.py` | Unit + regression tests |

## Runtime data (not code dependencies)

The job's defined input is the scheduler's saved definitions on the run
host, resolved at runtime (no path literals in code, per CRON-001):

- `CRON_DEFS_DIR` env, else `<home>/workspace/cron.d`
- `CRON_GOALS_DIR` env, else `<home>/workspace/goals`

GitHub auth uses the Muse-runtime credential surrogate (`custom.github`)
via `/opt/hatch/skills/skill-creator/bin/dynamic_credentials.py`, same as
the original script.

## Reply contract

- No change: `no changes.`
- Committed: `<commit-sha> <n> files changed`
- Error: brief error text, non-zero exit.

Never creates, edits, or deletes a cron definition to "fix" a diff — the
scheduler is the source of truth; this job mirrors one way.
