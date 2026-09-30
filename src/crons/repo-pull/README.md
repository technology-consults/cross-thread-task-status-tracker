# repo-pull

*Job package for the versioned-cron architecture. Created: 2026-09-30 · Last modified: 2026-09-30*

Daily (06:00 America/Toronto) fast-forward of every local repo clone on the
run host. Safety rule (unchanged from the original): a repo with uncommitted
local changes is SKIPPED, never overwritten; `merge --ff-only` only — never
`reset --hard`. Nothing is committed; the scheduler and remotes are untouched.

## Layout

| File | What it is |
|---|---|
| `run.py` | Package entrypoint: runs the vendored script, relays its output |
| `pull_all_repos.sh` | Vendored from `scripts/pull_all_repos.sh` (2026-09-30); `REPOS_DIR` only |
| `tests/test_pull.py` | Unit + functional tests |

## Runtime data (not code dependencies)

- `CRON_REPOS_DIR` env, else `$HOME/workspace/repos` on the run host.

## Reply contract

One line per repo, printed by the script and relayed verbatim:
`OK` (already current), `PULLED`, `SKIP` (with reason), `FAIL` (with error).
