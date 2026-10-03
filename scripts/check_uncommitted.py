#!/usr/bin/env python3
"""Timely commit check: flag workspace-only uncommitted work across repos.

Scans every clone under ~/workspace/repos/. For each repo with
`git status --porcelain` output (outside __pycache__), it compares each
changed file's worktree hash against the remote blob via the GitHub API:
  - matches remote  -> phantom flag (API commit moved remote, local HEAD
                       stale); not a problem, ignored.
  - differs         -> real uncommitted change; flagged with the file's age.

Prints one line per repo with real uncommitted changes, plus a summary.
Exit 0 = all clear (or only phantoms). Exit 1 = real uncommitted work found.

Usage: python3 check_uncommitted.py [--json]
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, os.path.join(REPO_ROOT, "..", "agent-tools", "scripts"))
from api_repo_sync import (  # noqa: E402
    api, parse_owner_repo, run_git, clean_bytecode)

REPOS_DIR = os.environ.get("WORKBENCH_REPOS_DIR", "/home/hatch/workspace/repos")


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def worktree_hash(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        raw = f.read()
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def remote_blob_sha(owner: str, repo: str, path: str):
    """Blob SHA of path on remote main, or None if absent/error."""
    try:
        r = api("GET", "/repos/%s/%s/contents/%s?ref=main"
                % (owner, repo, path))
        if isinstance(r, dict) and r.get("encoding") == "base64":
            raw = base64.b64decode(r["content"])
            return blob_sha(raw)
    except Exception:
        pass
    return None


def check_repo(repo_dir: str, name: str):
    """Return list of (path, age_hours) with real uncommitted changes."""
    if not os.path.isdir(os.path.join(repo_dir, ".git")):
        return [("<no .git — not a managed clone>", 0)]

    _, remote_url, _ = run_git(repo_dir, "config", "--get",
                               "remote.origin.url")
    parsed = parse_owner_repo(remote_url)
    if not parsed:
        return [("<unparseable remote>", 0)]
    owner, repo = parsed

    _, out, _ = run_git(repo_dir, "status", "--porcelain")
    changed = []
    for line in out.splitlines():
        if "__pycache__" in line:
            continue
        # porcelain v1: XY<space>path (or "R  old -> new")
        path = line[3:].split(" -> ")[-1].strip().strip('"')
        if path:
            changed.append((line[:2], path))

    flagged = []
    now = time.time()
    for _st, path in changed:
        full = os.path.join(repo_dir, path)
        if not os.path.isfile(full):
            # Deleted locally: real change unless also deleted on remote.
            if remote_blob_sha(owner, repo, path) is None:
                continue  # deleted on both sides; phantom
            age = (now - os.path.getmtime(repo_dir)) / 3600
            flagged.append((path + " (deleted locally)", age))
            continue
        try:
            local_sha = worktree_hash(full)
        except OSError:
            continue
        if local_sha == remote_blob_sha(owner, repo, path):
            continue  # phantom: content already on remote main
        try:
            age = (now - os.path.getmtime(full)) / 3600
        except OSError:
            age = -1
        flagged.append((path, age))
    return flagged


def main(argv):
    as_json = "--json" in argv
    report = {}
    for entry in sorted(os.listdir(REPOS_DIR)):
        repo_dir = os.path.join(REPOS_DIR, entry)
        if not os.path.isdir(repo_dir):
            continue
        flagged = check_repo(repo_dir, entry)
        if flagged:
            report[entry] = [{"path": p, "age_hours": round(a, 1)}
                             for p, a in flagged]

    if as_json:
        print(json.dumps(report, indent=2))
        return 1 if report else 0

    if not report:
        print("All clear: no real uncommitted work in any repo "
              "(phantoms and caches ignored).")
        return 0

    print("Repos with real uncommitted work:")
    for name, files in report.items():
        print("  %s:" % name)
        for f in files:
            age = ("%.1fh old" % f["age_hours"]
                   if f["age_hours"] >= 0 else "age unknown")
            print("    - %s (%s)" % (f["path"], age))
    print("%d repo(s) need attention." % len(report))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
