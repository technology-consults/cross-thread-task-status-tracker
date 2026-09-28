#!/usr/bin/env python3
"""Sync saved cron definitions into the cross-thread-task-status-tracker repo.

One-way mirror: scheduler -> ~/workspace/cron.d (+ ~/workspace/goals/*/crons)
-> repo crons/. The scheduler holds the source of truth; these files are its
read-only copies. Commits via the GitHub API as a SINGLE commit, and only
when something actually changed.

Usage: sync_crons_to_git.py [--dry-run]
"""
import base64
import hashlib
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

REPO = "technology-consults/cross-thread-task-status-tracker"
BRANCH = "main"
CRON_D = "/home/hatch/workspace/cron.d"
GOALS = "/home/hatch/workspace/goals"
DEST = "crons"
TZ = ZoneInfo("America/Toronto")

README = """# Cron definitions

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
"""


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        "https://api.github.com" + path, data=data, method=method,
        headers={"User-Agent": "muse-agent",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        print(f"GitHub API {method} {path} -> HTTP {e.code}: {e.read().decode()}",
              file=sys.stderr)
        sys.exit(1)


def blob_sha(data: bytes) -> str:
    h = hashlib.sha1()
    h.update(f"blob {len(data)}\0".encode())
    h.update(data)
    return h.hexdigest()


def collect():
    """Return {repo_path: bytes} for every definition file."""
    files = {}
    sources = [("shared", CRON_D)]
    if os.path.isdir(GOALS):
        for slug in sorted(os.listdir(GOALS)):
            cdir = os.path.join(GOALS, slug, "crons")
            if os.path.isdir(cdir):
                sources.append((f"goals/{slug}", cdir))
    for bucket, src in sources:
        for root, dirs, names in os.walk(src):
            dirs[:] = sorted(d for d in dirs if d != "_invalid")
            for n in sorted(names):
                if not n.endswith(".md"):
                    continue
                full = os.path.join(root, n)
                rel = os.path.relpath(full, src)
                with open(full, "rb") as f:
                    files[f"{DEST}/{bucket}/{rel}"] = f.read()
    files[f"{DEST}/README.md"] = README.encode()
    return files


def main():
    dry_run = "--dry-run" in sys.argv
    local = collect()

    ref = api("GET", f"/repos/{REPO}/git/ref/heads/{BRANCH}")
    base_sha = ref["object"]["sha"]
    tree = api("GET", f"/repos/{REPO}/git/trees/{base_sha}?recursive=1")
    remote = {t["path"]: t["sha"] for t in tree.get("tree", [])
              if t["type"] == "blob" and t["path"].startswith(DEST + "/")}

    changed, deleted = [], []
    for path, data in local.items():
        if remote.get(path) != blob_sha(data):
            changed.append(path)
    for path in remote:
        if path not in local:
            deleted.append(path)

    if not changed and not deleted:
        print("no changes")
        return

    print(f"changed/new: {len(changed)}, deleted: {len(deleted)}")
    if dry_run:
        for p in changed:
            print(f"  + {p}")
        for p in deleted:
            print(f"  - {p}")
        return

    entries = []
    for path in changed:
        b = api("POST", f"/repos/{REPO}/git/blobs",
                {"content": base64.b64encode(local[path]).decode(),
                 "encoding": "base64"})
        entries.append({"path": path, "mode": "100644",
                        "type": "blob", "sha": b["sha"]})
        print(f"  blob {path}")
    for path in deleted:
        entries.append({"path": path, "mode": "100644",
                        "type": "blob", "sha": None})
        print(f"  delete {path}")

    new_tree = api("POST", f"/repos/{REPO}/git/trees",
                   {"base_tree": tree["sha"], "tree": entries})
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z")
    msg = (f"Crons: sync {len(local)} definitions ({now})"
           + (f" — {len(deleted)} removed" if deleted else ""))
    commit = api("POST", f"/repos/{REPO}/git/commits",
                 {"message": msg, "tree": new_tree["sha"],
                  "parents": [base_sha]})
    # NOTE: git-refs path is PLURAL — the singular /git/ref/... drops PATCH.
    api("PATCH", f"/repos/{REPO}/git/refs/heads/{BRANCH}",
        {"sha": commit["sha"]})
    print(f"committed {commit['sha'][:8]}: {msg}")


if __name__ == "__main__":
    main()
