#!/usr/bin/env python3
"""Pre-commit board-integrity gate for the cross-thread-task-status-tracker.

tasks.json is written concurrently by API commits from several agents.
One malformed write breaks every reader (the board page, the digests,
the regression suite). This gate validates the whole new tasks.json
whenever it appears in a commit diff -- not just the added lines,
because a concurrent writer's mistake can sit anywhere in the file.

Reads a diff on stdin as JSON:
    {"files": {"<repo-rel path>": {"is_new": bool,
                                   "added": [[lineno, line], ...]}}}
argv[1] is the repo root (used to read the working-tree tasks.json).

Prints one line per violation:
    BLOCKED [<gate>] <path>:<lineno>: <snippet>
Exit 0 when clean, 1 on violations, 2 on usage/internal error.

Gates are documented on GATE_DEFS below; scripts/enforce/gates.json
mirrors that registry and a unit test enforces the match. Stdlib only.

The deliberate-act escape is the allowlist file
(scripts/enforce/allowlist_board.txt). A missing allowlist file fails
closed (exempts nothing).
"""
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Gate registry: (name, one-line description, allowlist relpath or None).
# ---------------------------------------------------------------------------
GATE_DEFS = [
    ("tasks-schema",
     "tasks.json must stay valid JSON with the board's task shape: "
     "required fields, unique string ids, known statuses, threads "
     "that exist, blockedBy as task id(s) or reference objects",
     "scripts/enforce/allowlist_board.txt"),
]

TASKS_JSON = "tasks.json"
INDEX_HTML = "index.html"

# Fields every task must carry. Deliberately the always-present core:
# the board readers need id/thread/title/status, and detail/updated are
# written by every producer. Optional fields (due, where, assigned_to,
# created, blockedBy, priority, ...) stay optional.
REQUIRED_FIELDS = {"id", "thread", "title", "status", "updated", "detail"}

# Fallback status set when index.html cannot be read. Mirrors the
# statuses observed on the board 2026-09-30.
_FALLBACK_STATUSES = {
    "approved", "blocked", "completed", "done", "in_progress", "parked",
    "pending_review", "pending_review_post_discussion", "rejected", "todo",
}

# Cap on per-task violations so one bad file cannot flood the output.
_MAX_TASK_VIOLATIONS = 25


def load_allowlist(repo_root, rel):
    """Set of exempt paths/prefixes; empty (fail closed) when unavailable."""
    if not rel:
        return set()
    try:
        with open(os.path.join(repo_root, rel), encoding="utf-8") as f:
            return {ln.strip() for ln in f
                    if ln.strip() and not ln.strip().startswith("#")}
    except OSError:
        print("warning: allowlist %s missing; no exemptions" % rel,
              file=sys.stderr)
        return set()


def is_exempt(path, allow):
    if path in allow:
        return True
    return any(path.startswith(p) for p in allow if p.endswith("/"))


def known_statuses(repo_root):
    """Status values the board page understands.

    Read from the STATUS table in index.html (same source the
    regression suite uses); fall back to the last observed set when
    the page cannot be read.
    """
    try:
        with open(os.path.join(repo_root, INDEX_HTML),
                  encoding="utf-8") as f:
            html = f.read()
    except OSError:
        return set(_FALLBACK_STATUSES)
    m = re.search(r"const STATUS\s*=\s*\{(.*?)\n\};", html, re.DOTALL)
    if not m:
        return set(_FALLBACK_STATUSES)
    found = set(re.findall(r"^\s*(\w+):", m.group(1), re.MULTILINE))
    return found or set(_FALLBACK_STATUSES)


def _blocked_by_entry_ok(x):
    """One blockedBy entry is valid when it is a non-empty task-id string
    or a reference object the board reader resolves: {"kind": "task",
    "id": "<task id>"} or {"kind": "external", "note": "<text>"}.
    (index.html computes blockers via b.id; the unblock watcher
    tolerates both the string and object forms, so the gate must too.)"""
    if isinstance(x, str):
        return bool(x)
    if isinstance(x, dict):
        kind = x.get("kind")
        if kind == "task":
            return isinstance(x.get("id"), str) and bool(x.get("id"))
        if kind == "external":
            return isinstance(x.get("note"), str) and bool(x.get("note"))
    return False


def check_tasks_schema(diff, repo_root, allow):
    """Validate the whole new tasks.json when it is in the diff."""
    if TASKS_JSON not in diff["files"]:
        return []
    if is_exempt(TASKS_JSON, allow):
        return []
    out = []

    def blocked(lineno, snippet):
        out.append(("tasks-schema", TASKS_JSON, lineno, snippet[:120]))

    full = os.path.join(repo_root, TASKS_JSON)
    try:
        with open(full, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        blocked(0, "tasks.json is not valid JSON: %s" % str(e)[:100])
        return out
    if not isinstance(data, dict):
        blocked(0, "tasks.json top level must be an object")
        return out
    tasks = data.get("tasks")
    threads = data.get("threads")
    if not isinstance(tasks, list):
        blocked(0, '"tasks" must be a list')
        return out
    if not isinstance(threads, dict):
        blocked(0, '"threads" must be an object')
        return out
    if not tasks:
        blocked(0, '"tasks" is empty: a board wipe needs a deliberate '
                   "allowlist entry")
        return out
    statuses = known_statuses(repo_root)
    seen_ids = set()
    for i, task in enumerate(tasks):
        if len(out) >= _MAX_TASK_VIOLATIONS:
            blocked(0, "... further violations truncated")
            break
        where = "task[%d]" % i
        if not isinstance(task, dict):
            blocked(0, "%s is not an object" % where)
            continue
        missing = REQUIRED_FIELDS - set(task.keys())
        if missing:
            blocked(0, "%s missing required fields: %s"
                    % (where, ",".join(sorted(missing))))
        tid = task.get("id")
        if not isinstance(tid, str) or not tid:
            blocked(0, "%s has a non-string/empty id" % where)
        elif tid in seen_ids:
            blocked(0, "duplicate task id: %s" % tid)
        else:
            seen_ids.add(tid)
        status = task.get("status")
        if isinstance(status, str) and status not in statuses:
            blocked(0, "%s has unknown status %r" % (where, status))
        thread = task.get("thread")
        if isinstance(thread, str) and thread not in threads:
            blocked(0, "%s references unknown thread %r" % (where, thread))
        blocked_by = task.get("blockedBy")
        if blocked_by is not None:
            entries = (blocked_by if isinstance(blocked_by, list)
                       else [blocked_by])
            if not all(_blocked_by_entry_ok(x) for x in entries):
                blocked(0, "%s has a malformed blockedBy (want a task id, "
                           "a list of task ids, or reference objects "
                           '{"kind": "task", "id": ...} / '
                           '{"kind": "external", "note": ...})' % where)
    return out


# --- entry point -------------------------------------------------------------

_CHECKS = {
    "tasks-schema": check_tasks_schema,
}


def check_all(diff, repo_root):
    allowlists = {name: load_allowlist(repo_root, rel)
                  for name, _desc, rel in GATE_DEFS}
    out = []
    for name, _desc, _rel in GATE_DEFS:
        out.extend(_CHECKS[name](diff, repo_root, allowlists[name]))
    return out


def read_diff():
    try:
        raw = sys.stdin.read()
    except OSError as e:
        print("error: cannot read stdin: %s" % e, file=sys.stderr)
        sys.exit(2)
    try:
        diff = json.loads(raw)
    except ValueError as e:
        print("error: invalid diff JSON: %s" % e, file=sys.stderr)
        sys.exit(2)
    if not isinstance(diff, dict) or "files" not in diff:
        print("error: diff JSON needs a 'files' object", file=sys.stderr)
        sys.exit(2)
    return diff


def main(argv):
    if len(argv) != 2:
        print("usage: %s <repo-root> < diff.json" % argv[0], file=sys.stderr)
        return 2
    violations = check_all(read_diff(), argv[1])
    for gate, path, lineno, snippet in violations:
        print("BLOCKED [%s] %s:%d: %s" % (gate, path, lineno, snippet))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
