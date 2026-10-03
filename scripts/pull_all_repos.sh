#!/bin/bash
# Workbench sync: bring every local repo clone to origin/main.
#
# GitHub operations are API-only (standing rule): git is used only for local
# operations (status, rev-parse, add, commit). The network path is always the
# GitHub API, via scripts/api_repo_sync.py — one mechanism for every repo,
# public or private. There is no git-fetch path.
#
# Safety rule: a repo with uncommitted local changes is SKIPPED, never
# overwritten. The sync commit api_repo_sync.py makes is local-only and is
# never pushed. `__pycache__` bytecode caches are ignored by the dirty check.
set -u
REPOS_DIR="/home/hatch/workspace/repos"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for repo in "$REPOS_DIR"/*/; do
    name=$(basename "$repo")
    if [ ! -d "$repo/.git" ]; then
        echo "SKIP $name: not a git repo"
        continue
    fi
    python3 "$SCRIPT_DIR/api_repo_sync.py" "$repo" "$name"
done
