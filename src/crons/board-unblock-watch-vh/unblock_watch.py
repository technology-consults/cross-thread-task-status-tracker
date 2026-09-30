#!/usr/bin/env python3
"""Board unblock watcher (vendored, adapted for the versioned-cron package).

Behavior-preserving move of unblock_watch.py previously at the repo root,
with these package adaptations:
- tasks.json is fetched from the repo via the GitHub API (api.github.com
  only), never from a local checkout.
- State (handled ids) lives in CRON_JOB_STATE_DIR, else
  <home>/.cron_runner/job_state/<CRON_JOB_NAME or board-unblock-watch>/;
  on first use it is seeded once from the legacy workspace copy
  (<home>/workspace/repos/cross-thread-task-status-tracker/hidden_files/
  unblock_watch_state.json). Paths are constructed at runtime; no
  workspace literals in code.
- New --mark-handled flag records handled task ids after the agent acts.

A task is actionable when:
- status is 'todo', 'blocked', or 'blocked_approved', AND
- every blockedBy entry of kind 'task' points to a task with status 'done', AND
- every blockedBy entry of kind 'external' has a verifiable gate date that has arrived
  (gate = ISO date in the note, else the task's 'due' field; no date -> still blocked), AND
- no 'start' field dated in the future.

A task that never had any blockers or start gate is never surfaced here: with
nothing that could have blocked it there is no unblock event, and brand-new
todos are announced by the board publish flow. (2026-09-29: a never-gated todo
was misreported as an "unblock notice".)

Prints a JSON list of newly actionable tasks, excluding ids already recorded
in the state file. The caller (run.py / agent) decides per task whether the
work is mine to do or BalRam's step, acts accordingly, then records handled
ids via --mark-handled.

With --sweep, additionally prints tasks the hourly unblock check would never
re-surface:
- reason "idle": status todo, blockers already clear, never handled
  (covers state resets, downtime, or a pickup the worker never completed).
- reason "stalled": status in_progress, last update over STALL_DAYS ago,
  not recurring/standing work. Report-only: the caller must NOT auto-act,
  only surface a brief note naming the task and its last-update date.
- reason "completed_stalled": status completed, last update over a day ago —
  the post-review actions (push/tag/deploy) should finish the same day, so an
  older completed task means the automation failed or stalled. Report-only:
  surface a brief note naming the task and its last-update date.

Each sweep entry carries "reason" and an "owner_hint" ("his" when the task is
assigned to BalRam, else "mine").
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from github_api import get_contents  # noqa: E402

REPO = "technology-consults/cross-thread-task-status-tracker"
TASKS_PATH = "tasks.json"
LEGACY_STATE_PARTS = ("workspace", "repos",
                      "cross-thread-task-status-tracker",
                      "hidden_files", "unblock_watch_state.json")

ISO = re.compile(r"(\d{4}-\d{2}-\d{2})")
STALL_DAYS = 3
RECURRING = re.compile(r"\b(daily|weekly|recurring|standing|ongoing|cron|digest|watchdog)\b", re.I)
HIS_STEP = re.compile(r"\(yours\)|\bhis step\b|balram'?s step", re.I)


def home():
    return os.path.expanduser("~")


def state_path():
    override = os.environ.get("CRON_JOB_STATE_DIR")
    if override:
        os.makedirs(override, exist_ok=True)
        return os.path.join(override, "unblock_watch_state.json")
    job = os.environ.get("CRON_JOB_NAME", "board-unblock-watch")
    d = os.path.join(home(), ".cron_runner", "job_state", job)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "unblock_watch_state.json")


def legacy_state_path():
    return os.path.join(home(), *LEGACY_STATE_PARTS)


def load_state():
    """Handled-ids state; seeds once from the legacy workspace copy."""
    p = state_path()
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        pass
    state = {"handled": [], "note": "seeded from legacy workspace copy"}
    try:
        with open(legacy_state_path(), encoding="utf-8") as f:
            legacy = json.load(f)
        if isinstance(legacy, dict) and isinstance(
                legacy.get("handled"), list):
            state["handled"] = legacy["handled"]
    except (OSError, ValueError):
        pass
    save_state(state)
    return state


def save_state(state):
    with open(state_path(), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def mark_handled(ids):
    state = load_state()
    handled = set(state.get("handled", []))
    handled.update(ids)
    state["handled"] = sorted(handled)
    save_state(state)
    return state["handled"]


def load_tasks():
    text, _ = get_contents(REPO, TASKS_PATH)
    data = json.loads(text)
    items = data if isinstance(data, list) else data.get("tasks",
                                                         data.get("items",
                                                                  []))
    return items


def blockers_clear(t, byid, today):
    for b in t.get("blockedBy") or []:
        if isinstance(b, str):
            b = {"kind": "task", "id": b}  # legacy bare task-id entries (2026-09-30)
        kind = b.get("kind")
        if kind == "task":
            ref = byid.get(b.get("id"))
            if not (ref and ref.get("status") == "done"):
                return False
        elif kind == "external":
            m = ISO.search(b.get("note", "") or "")
            gate = m.group(1) if m else t.get("due")
            if not gate or gate > today:
                return False
        # unknown kinds: ignore (don't block on what we can't interpret)
    start = t.get("start")
    if start and start > today:
        return False
    return True


def owner_hint(t):
    if t.get("assigned_to") == "BalRam":
        return "his"
    if t.get("assigned_to") == "Bandhu":
        return "mine"
    text = " ".join(str(t.get(k) or "") for k in ("title", "detail"))
    return "his" if HIS_STEP.search(text) else "mine"


def was_gated(t):
    """True when the task ever had something that could block it.

    A task with no blockedBy entries and no start gate was never blocked, so
    it can never "become" actionable -- it was always actionable. Such tasks
    are announced by the board publish flow, never by this watcher.
    """
    return bool(t.get("blockedBy")) or bool(t.get("start"))


FIELDS = ("id", "thread", "title", "status", "due", "detail", "where",
          "assigned_to")


def compute_unblocks(items, handled, thread, today):
    byid = {t.get("id"): t for t in items}
    out = []
    for t in items:
        tid = t.get("id")
        if not tid or tid in handled:
            continue
        if thread and t.get("thread") != thread:
            continue
        if t.get("status") not in ("todo", "blocked", "blocked_approved"):
            continue
        if not blockers_clear(t, byid, today):
            continue
        if not was_gated(t):
            continue  # never gated: nothing ever blocked it, no unblock event
        out.append({k: t.get(k) for k in FIELDS})
    return out


def compute_sweep(items, handled, thread, today, stall_cutoff):
    byid = {t.get("id"): t for t in items}
    out = []
    for t in items:
        tid = t.get("id")
        if not tid or tid in handled:
            continue
        if thread and t.get("thread") != thread:
            continue
        status = t.get("status")
        if status == "todo" and blockers_clear(t, byid, today):
            if not was_gated(t):
                continue  # never gated: publish flow announces new todos
            entry = {k: t.get(k) for k in FIELDS}
            entry.update(reason="idle", owner_hint=owner_hint(t))
            out.append(entry)
        elif status == "in_progress":
            text = " ".join(str(t.get(k) or "") for k in ("title", "detail"))
            if RECURRING.search(text):
                continue
            upd = t.get("updated") or ""
            if upd and upd >= stall_cutoff:
                continue
            entry = {k: t.get(k) for k in FIELDS}
            entry.update(reason="stalled", owner_hint=owner_hint(t))
            out.append(entry)
        elif status == "completed":
            upd = t.get("updated") or ""
            if upd and upd >= today:
                continue  # completed today: post-actions may still be running
            entry = {k: t.get(k) for k in FIELDS}
            entry.update(reason="completed_stalled", owner_hint=owner_hint(t))
            out.append(entry)
    return out


def today_local():
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    # The VM runs on UTC; BalRam's day (America/Toronto) is what "today",
    # staleness, and date gates mean.
    now_local = datetime.now(ZoneInfo("America/Toronto")).date()
    return (now_local.isoformat(),
            (now_local - timedelta(days=STALL_DAYS)).isoformat())


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--thread", default=None,
                    help="only consider tasks with this thread value (sv, tr, vh)")
    ap.add_argument("--sweep", action="store_true",
                    help="list idle todo tasks and possibly-stalled tasks, with reason + owner_hint")
    ap.add_argument("--mark-handled", default=None,
                    help="JSON array of task ids to record as handled")
    args = ap.parse_args(argv)

    if args.mark_handled is not None:
        ids = json.loads(args.mark_handled)
        print(json.dumps({"handled": mark_handled(ids)}, indent=1))
        return 0

    today, stall_cutoff = today_local()
    items = load_tasks()
    handled = set(load_state().get("handled", []))
    if args.sweep:
        out = compute_sweep(items, handled, args.thread, today, stall_cutoff)
    else:
        out = compute_unblocks(items, handled, args.thread, today)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
