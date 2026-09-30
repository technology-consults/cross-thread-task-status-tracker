#!/usr/bin/env python3
"""task-due-date-watch — versioned package entrypoint (run.py).

Behavior-preserving move of the cron body previously executed by the agent:

1. (script) GET tasks.json from the tracker repo via the GitHub API,
   bucket non-agreed/non-rejected tasks with due dates by days-until-due
   (Toronto date), refresh meta.asOf to today via PUT when stale.
2. (agent, handshake) if any thread has flagged tasks, ask the agent to
   send ONE message per thread to that thread's task-tracker chat.
3. (script) validate the agent result, append the daily-log line when
   anything was posted or the asOf push failed, print the final summary.

Handshake: exit 10 + @@AGENT-REQUEST-BEGIN@@ ... @@AGENT-REQUEST-END@@.
Max 5 agent rounds; afterwards exit 20 (fail loudly, never partial).
"""
import argparse
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from github_api import get_contents, put_contents, GitHubError  # noqa: E402

JOB = "task-due-date-watch"
REPO = "technology-consults/cross-thread-task-status-tracker"
TASKS_PATH = "tasks.json"
TZ = ZoneInfo("America/Toronto")

# Thread -> task-tracker chat (from the job definition; stable ids).
TRACKER_CHATS = {
    "sv": ("d82796e3-56f1-4d34-bf51-665165a38e92", "Short Video"),
    "tr": ("1ff0cb94-8438-4900-8c47-a39846cbf1a3", "Trading"),
    "vh": ("547fb3d1-6b69-4410-b9d0-084cd478e7ff", "Vehicle"),
}

REQ_BEGIN = "@@AGENT-REQUEST-BEGIN@@"
REQ_END = "@@AGENT-REQUEST-END@@"
HANDSHAKE_EXIT = 10
FAIL_EXIT = 20
MAX_ROUNDS = 5

ALERT_SCHEMA = {
    "type": "object",
    "properties": {
        "posted": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "object"},
    },
    "required": ["posted"],
}


def today_str():
    return datetime.now(TZ).date().isoformat()


def bucket(days):
    if days < 0:
        return "OVERDUE"
    if days == 0:
        return "DUE TODAY"
    if days <= 2:
        return "DUE WITHIN 2 DAYS"
    if days <= 7:
        return "DUE THIS WEEK"
    return None


def flagged_by_thread(tasks, today):
    """Return {thread: [lines]} for tasks needing an alert."""
    out = {}
    for t in tasks:
        if t.get("status") in ("agreed", "rejected"):
            continue
        due = t.get("due")
        if not due:
            continue
        try:
            days = (datetime.strptime(due, "%Y-%m-%d").date()
                    - datetime.strptime(today, "%Y-%m-%d").date()).days
        except ValueError:
            continue
        b = bucket(days)
        if not b:
            continue
        thread = t.get("thread") or "sv"
        out.setdefault(thread, []).append(
            "%s | %s | due %s | %s"
            % (t.get("id"), t.get("title"), due, b))
    return out


def refresh_asof(doc, today):
    """Set meta.asOf to today; return (changed, doc)."""
    meta = doc.setdefault("meta", {})
    if meta.get("asOf") == today:
        return False, doc
    meta["asOf"] = today  # lastUpdated untouched: it records data changes
    return True, doc


def validate_result(result, schema):
    """Tiny schema check: required keys present, basic types match."""
    if not isinstance(result, dict):
        return "result is not a JSON object"
    for key in schema.get("required", ()):
        if key not in result:
            return "missing required key %r" % key
    props = schema.get("properties", {})
    for key, spec in props.items():
        if key not in result:
            continue
        val = result[key]
        want = spec.get("type")
        if want == "array" and not isinstance(val, list):
            return "%r must be an array" % key
        if want == "object" and not isinstance(val, dict):
            return "%r must be an object" % key
        if want == "string" and not isinstance(val, str):
            return "%r must be a string" % key
    return None


def emit_request(task, schema, attempt):
    print(REQ_BEGIN)
    print(json.dumps({"need": "agent-step", "task": task,
                      "schema": schema, "attempt": attempt}, indent=2))
    print(REQ_END)
    return HANDSHAKE_EXIT


def build_alert_task(flagged):
    parts = [
        "Due-date alerts for the All Threads Status Board.",
        "For EACH thread below, send ONE chat message to that thread's "
        "task-tracker chat, addressed to that chat's agent, asking it to "
        "post the alert lines to the user in that chat. Keep each alert "
        "compact: one line per task (task id, title, due date, bucket). "
        "Threads with nothing flagged get no message.",
    ]
    for thread, lines in sorted(flagged.items()):
        chat_id, name = TRACKER_CHATS.get(thread, (None, thread))
        parts.append("Thread %s (%s) -> chat %s:" % (thread, name, chat_id))
        parts.extend("  " + ln for ln in lines)
    parts.append(
        'Reply with JSON matching the schema: {"posted": [<chat ids you '
        'posted to>], "notes": {<chat id>: <note>}}. "posted" is required.')
    return "\n".join(parts)


def state_dir():
    override = os.environ.get("CRON_JOB_STATE_DIR")
    if override:
        os.makedirs(override, exist_ok=True)
        return override
    d = os.path.join(os.path.expanduser("~"), ".cron_runner", "job_state",
                     JOB)
    os.makedirs(d, exist_ok=True)
    return d


def round_state_path():
    return os.path.join(state_dir(), "round.json")


def save_round_state(flagged, today, attempt):
    with open(round_state_path(), "w", encoding="utf-8") as f:
        json.dump({"flagged": flagged, "today": today, "attempt": attempt},
                  f)


def load_round_state():
    try:
        with open(round_state_path(), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def clear_round_state():
    try:
        os.remove(round_state_path())
    except OSError:
        pass


def append_daily_log(today, line):
    mem_dir = os.environ.get("CRON_MEMORY_DIR") or os.path.join(
        os.path.expanduser("~"), "memory")
    os.makedirs(mem_dir, exist_ok=True)
    path = os.path.join(mem_dir, "%s.md" % today)
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n- %s\n" % line)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-result", default=None)
    args = ap.parse_args(argv)
    today = today_str()

    if args.agent_result is None:
        # Round 0 (script): fetch, bucket, refresh asOf.
        try:
            text, sha = get_contents(REPO, TASKS_PATH)
            doc = json.loads(text)
        except (GitHubError, ValueError) as e:
            print("ERROR fetching tasks.json: %s" % e)
            return 1
        tasks = doc.get("tasks", [])
        flagged = flagged_by_thread(tasks, today)
        changed, doc = refresh_asof(doc, today)
        asof_note = ""
        if changed:
            try:
                put_contents(REPO, TASKS_PATH, json.dumps(doc, indent=2,
                                                         ensure_ascii=False),
                             sha, "Daily board date refresh: asOf %s" % today)
                asof_note = "asOf refreshed to %s" % today
            except GitHubError as e:
                print("asOf push FAILED: %s" % e)
                append_daily_log(today, "task-due-date-watch: asOf push "
                                       "failed: %s" % e)
                # continue: alerts still go out; final message notes failure
                asof_note = "asOf push FAILED"
        else:
            asof_note = "asOf already %s" % today

        if not flagged:
            print("watch ran, zero tasks flagged, %s - routine, nothing "
                  "for the user to see." % asof_note)
            return 0
        # Hand the alert delivery to the agent; persist round state so a
        # retry rebuilds the same task.
        save_round_state(flagged, today, 1)
        return emit_request(build_alert_task(flagged), ALERT_SCHEMA, 1)

    # Agent-result rounds (script): validate, log, summarize.
    state = load_round_state()
    if state is None:
        print("ERROR: no round state; cannot match an agent result to a "
              "request. Failing loudly.")
        return FAIL_EXIT
    attempt = state.get("attempt", 1)
    flagged = state.get("flagged", {})
    today = state.get("today", today)
    try:
        result = json.loads(args.agent_result)
        err = validate_result(result, ALERT_SCHEMA)
    except ValueError as e:
        err = "result is not valid JSON: %s" % e
    if err:
        if attempt >= MAX_ROUNDS:
            clear_round_state()
            print("agent result invalid after %d rounds (%s); failing "
                  "loudly, no partial delivery." % (MAX_ROUNDS, err))
            return FAIL_EXIT
        save_round_state(flagged, today, attempt + 1)
        task = ("Your last result was invalid (%s). Try again - same "
                "alerts as before:\n\n" % err) + build_alert_task(flagged)
        return emit_request(task, ALERT_SCHEMA, attempt + 1)
    posted = result.get("posted", [])
    clear_round_state()
    if posted:
        append_daily_log(today, "task-due-date-watch: posted due-date "
                               "alerts to %d thread chat(s): %s"
                               % (len(posted), ", ".join(posted)))
    n_threads = len(flagged)
    print("watch ran, %d thread(s) flagged, alerts posted to %d chat(s)."
          % (n_threads, len(posted)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
