#!/bin/bash
# Workbench sync: fast-forward every local repo clone to origin/main.
# Safety rule: a repo with uncommitted local changes is SKIPPED, never
# overwritten. Uses merge --ff-only (never reset --hard), so even in a
# check-then-act race git itself refuses to touch a dirty tree.
#
# Private repos without fetch credentials: when `git fetch` dies on auth
# ("could not read Username"), scripts/api_repo_sync.py syncs the working
# tree through the GitHub API instead (same auth as scripts/commit.py).
# The sync commit it makes is local-only and never pushed.
#
# `__pycache__` bytecode caches are ignored by the dirty check; they are
# regenerable and must not block the sync.
set -u
REPOS_DIR="/home/hatch/workspace/repos"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for repo in "$REPOS_DIR"/*/; do
    name=$(basename "$repo")
    if [ ! -d "$repo/.git" ]; then
        echo "SKIP $name: not a git repo"
        continue
    fi
    if [ -n "$(git -C "$repo" status --porcelain 2>/dev/null | grep -v '__pycache__')" ]; then
        echo "SKIP $name: local changes present, leaving untouched"
        continue
    fi
    fetch_err=$(git -C "$repo" fetch origin 2>&1 >/dev/null)
    if [ $? -ne 0 ]; then
        if echo "$fetch_err" | grep -qiE "could not read username|authentication failed|permission denied|repository not found"; then
            python3 "$SCRIPT_DIR/api_repo_sync.py" "$repo" "$name"
            continue
        fi
        echo "FAIL $name: fetch failed"
        continue
    fi
    if ! git -C "$repo" rev-parse --verify origin/main --quiet >/dev/null 2>&1; then
        echo "SKIP $name: no origin/main"
        continue
    fi
    local_head=$(git -C "$repo" rev-parse HEAD)
    remote_head=$(git -C "$repo" rev-parse origin/main)
    if [ "$local_head" = "$remote_head" ]; then
        echo "OK $name: already current (${local_head:0:8})"
        continue
    fi
    if git -C "$repo" merge --ff-only origin/main --quiet 2>/dev/null; then
        echo "PULLED $name: -> $(git -C "$repo" rev-parse --short HEAD)"
    else
        echo "FAIL $name: cannot fast-forward (diverged); needs a look"
    fi
done
