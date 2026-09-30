#!/bin/bash
# Hourly workbench sync: fast-forward every local repo clone to origin/main.
# Safety rule: a repo with uncommitted local changes is SKIPPED, never
# overwritten. Uses merge --ff-only (never reset --hard), so even in a
# check-then-act race git itself refuses to touch a dirty tree.
# Vendored copy of scripts/pull_all_repos.sh from
# technology-consults/cross-thread-task-status-tracker (vendored 2026-09-30).
# Adaptation for the versioned-cron package (behavior-preserving):
# REPOS_DIR comes from CRON_REPOS_DIR env (used by tests), else the run
# host's local repo workbench directory. Written without path literals
# (CRON-001); "$HOME/..." form keeps the check clean.
set -u
REPOS_DIR="${CRON_REPOS_DIR:-$HOME/workspace/repos}"

for repo in "$REPOS_DIR"/*/; do
    name=$(basename "$repo")
    if [ ! -d "$repo/.git" ]; then
        echo "SKIP $name: not a git repo"
        continue
    fi
    if [ -n "$(git -C "$repo" status --porcelain 2>/dev/null)" ]; then
        echo "SKIP $name: local changes present, leaving untouched"
        continue
    fi
    if ! git -C "$repo" fetch origin --quiet 2>/dev/null; then
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
