#!/usr/bin/env python3
"""One-time migration to the 2026-09-28 board redesign (BalRam-approved spec).

Applies, per task:
- Status migration: agreed->done, blocked_agreed->blocked_approved,
  code_completed->blocked_completed, pending_me->todo (defensive; none exist),
  in_progress + "(yours)" + review-like title -> pending_review (assigned BalRam),
  in_progress + "(yours)" action step -> stays in_progress (assigned BalRam).
- assigned_to backfill: "(yours)" in title -> BalRam, else Bandhu.
- created backfill: keep existing value; for blanks, search git history of
  tasks.json for the task id's first appearance; leave blank if not found.

Idempotent: re-running changes nothing once migrated.
"""
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_JSON = os.path.join(BASE, "tasks.json")
REVIEW_LIKE = re.compile(r"\breview\b|\bapproval\b", re.I)


def git_first_seen():
    """Map task id -> first commit date (YYYY-MM-DD) it appeared in tasks.json."""
    log = subprocess.run(
        ["git", "log", "--reverse", "--format=%h %ad", "--date=short", "--", "tasks.json"],
        cwd=BASE, capture_output=True, text=True)
    first = {}
    for line in log.stdout.splitlines():
        sha, date = line.split(" ", 1)
        try:
            blob = subprocess.run(["git", "show", f"{sha}:tasks.json"],
                                  cwd=BASE, capture_output=True, text=True).stdout
            data = json.loads(blob)
            items = data["tasks"] if isinstance(data, dict) else data
            for t in items:
                tid = t.get("id")
                if tid and tid not in first:
                    first[tid] = date
        except (json.JSONDecodeError, KeyError):
            continue
    return first


def migrate(tasks):
    first_seen = git_first_seen()
    report = []
    for t in tasks:
        tid = t.get("id", "?")
        old_status = t.get("status")
        title = t.get("title") or ""
        yours = "(yours)" in title.lower()

        # assigned_to backfill
        if not t.get("assigned_to"):
            t["assigned_to"] = "BalRam" if yours else "Bandhu"
        # pending_review is BalRam's review task by definition
        if t.get("status") == "pending_review":
            t["assigned_to"] = "BalRam"

        # status migration
        new_status = old_status
        if old_status == "agreed":
            new_status = "done"  # BalRam 2026-09-28: old agreed meant finalized; keep it terminal
        elif old_status == "blocked_agreed":
            new_status = "blocked_approved"
        elif old_status == "code_completed":
            new_status = "blocked_completed"
        elif old_status == "pending_me":
            new_status = "todo"
            t["assigned_to"] = "Bandhu"
        elif old_status == "in_progress" and yours and REVIEW_LIKE.search(title):
            new_status = "pending_review"
            t["assigned_to"] = "BalRam"
        # (yours) action steps stay in_progress, assigned BalRam (set above)

        if new_status != old_status:
            t["status"] = new_status
            report.append(f"{tid}: {old_status} -> {new_status}")

        # created backfill
        if not t.get("created"):
            found = first_seen.get(tid)
            t["created"] = found or ""
            report.append(f"{tid}: created <- {found or '(blank: no git evidence)'}")

        t["updated"] = t.get("updated") or "2026-09-28"
    return report


def main():
    check = "--check" in sys.argv
    with open(TASKS_JSON) as f:
        data = json.load(f)
    tasks = data["tasks"]
    report = migrate(tasks)
    if check:
        print("\n".join(report) if report else "no changes needed")
        return
    with open(TASKS_JSON, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"migrated {len(report)} change(s):")
    print("\n".join(report))


if __name__ == "__main__":
    main()
