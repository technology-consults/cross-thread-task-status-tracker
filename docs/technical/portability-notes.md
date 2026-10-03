# Portability notes

Created: 2026-09-30. Last modified: 2026-10-03.

Code in this repo that only runs inside the Muse agent runtime is listed
here, one row per dependency. The `portability-row` enforcement gate
requires this file to be touched in the same commit that introduces a
new runtime-only dependency.

| Dependency | Used by | Why it is runtime-only |
|---|---|---|
| Muse runtime credential surrogate (`dynamic_credentials`, `/opt/hatch/skills/skill-creator/bin`) | `scripts/commit.py`, `push_board.py`, `scripts/push_board.py`, `scripts/api_repo_sync.py` | Supplies the GitHub API credential inside the agent runtime. Outside the runtime, set the `GITHUB_TOKEN` env var instead (`scripts/commit.py` prefers it when present). |
| Workbench clone directory (`~/workspace/repos/`) | `scripts/pull_all_repos.sh`, `scripts/api_repo_sync.py`, `scripts/check_uncommitted.py` | The workbench lives on this machine only. Outside the runtime, point `REPOS_DIR` at the local clone directory. |
