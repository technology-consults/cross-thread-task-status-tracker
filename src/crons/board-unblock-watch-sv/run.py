#!/usr/bin/env python3
"""board-unblock-watch-sv — versioned package entrypoint (run.py).

Behavior-preserving move of the cron body previously executed by the agent
(hourly, America/Toronto). Watches the sv thread's board tasks for
newly-unblocked work plus a sweep for idle/stalled tasks.

Track B: script-as-orchestrator.
- Script-driven: unblock detection and the idle/stalled/completed_stalled
  sweep (vendored unblock_watch.py, adapted to fetch tasks.json from this
  repo via the GitHub API), handled-id state, and the digest.
- Agent-driven (handshake): per-task decisions and actions — creating
  review tasks and unblock notices for BalRam's steps, doing my own work,
  marking statuses. The script cannot judge "his step vs mine" or perform
  the work; the agent is the callable service for that step.

Handshake: exit 10 with @@AGENT-REQUEST-BEGIN@@ JSON {need, task, schema,
attempt}; the agent returns handled/acted/errors; the script validates,
records handled ids, and reports. Max 5 rounds, then exit 20 (fail loudly,
never partial). If both lists are empty: stay silent, exit 0, no agent call.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

JOB = "board-unblock-watch-sv"
THREAD = "sv"
TRACKER_CHAT = "d82796e3-56f1-4d34-bf51-665165a38e92"

REQ_BEGIN = "@@AGENT-REQUEST-BEGIN@@"
REQ_END = "@@AGENT-REQUEST-END@@"
HANDSHAKE_EXIT = 10
FAIL_EXIT = 20
MAX_ROUNDS = 5

RESULT_SCHEMA = {
    "type": "object",
    "properties": {
        "handled": {"type": "array", "items": {"type": "string"}},
        "acted": {"type": "array", "items": {"type": "object"}},
        "errors": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["handled", "acted", "errors"],
}


def state_dir():
    override = os.environ.get("CRON_JOB_STATE_DIR")
    if override:
        os.makedirs(override, exist_ok=True)
        return override
    d = os.path.join(os.path.expanduser("~"), ".cron_runner", "job_state",
                     JOB)
    os.makedirs(d, exist_ok=True)
    return d


def round_path():
    return os.path.join(state_dir(), "round.json")


def run_watch(extra_args):
    env = dict(os.environ)
    env["CRON_JOB_STATE_DIR"] = state_dir()
    p = subprocess.run([sys.executable,
                        os.path.join(HERE, "unblock_watch.py"),
                        "--thread", THREAD] + extra_args,
                       capture_output=True, text=True, env=env)
    if p.returncode != 0:
        raise RuntimeError("unblock_watch.py failed: %s" % p.stderr.strip())
    return json.loads(p.stdout)


def validate_result(result):
    if not isinstance(result, dict):
        return "result is not a JSON object"
    if not isinstance(result.get("handled"), list):
        return "missing required key 'handled' (array of task-id strings)"
    if not all(isinstance(x, str) for x in result["handled"]):
        return "'handled' must be an array of task-id strings"
    if not isinstance(result.get("acted"), list):
        return "missing required key 'acted' (array)"
    if not isinstance(result.get("errors"), list):
        return "missing required key 'errors' (array)"
    for i, a in enumerate(result["acted"]):
        if not isinstance(a, dict):
            return "acted[%d] is not an object" % i
        for k in ("id", "action", "note"):
            if not isinstance(a.get(k), str):
                return "acted[%d].%s must be a string" % (i, k)
    return None


def emit_request(task, schema, attempt):
    print(REQ_BEGIN)
    print(json.dumps({"need": "agent-step", "task": task,
                      "schema": schema, "attempt": attempt}, indent=2))
    print(REQ_END)
    return HANDSHAKE_EXIT


def build_task(unblocks, sweep):
    return "\n".join([
        "Board unblock watch for the %s thread (hourly check)." % THREAD,
        "Newly unblocked tasks:",
        json.dumps(unblocks, indent=2),
        "",
        "Sweep findings (idle todo / stalled in_progress / "
        "completed_stalled):",
        json.dumps(sweep, indent=2),
        "",
        "For each task above, decide and act:",
        "- BalRam's step (assigned_to BalRam, or the title/detail says "
        "'(yours)' / 'his step' / \"BalRam's step\"): if status is todo and "
        "the detail is usable, create a review task in the %s thread and "
        "post an unblock notice to the %s tracker chat (ID %s). If there "
        "is no usable detail, still create the review task in the %s "
        "thread so he sees it." % (THREAD, THREAD, TRACKER_CHAT, THREAD),
        "- My work (assigned_to Bandhu, or no his-step marker): if status "
        "is todo, do the work, then mark it in_progress while working and "
        "completed when done.",
        "- Sweep entries (reason idle / stalled / completed_stalled): "
        "report-only. Do NOT auto-act; surface a brief note naming the "
        "task and its last-update date.",
        "- Record handled ids for every task you acted on or deliberately "
        "left alone; mark todo -> in_progress when you start my work.",
        'Reply with JSON: {"handled": ["<task id>", ...], "acted": '
        '[{"id": "<task id>", "action": "<what you did>", "note": '
        '"<outcome>"}], "errors": ["<anything that failed and why>"]}.',
    ])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-result", default=None)
    args = ap.parse_args(argv)

    if args.agent_result is None:
        try:
            unblocks = run_watch([])
            sweep = run_watch(["--sweep"])
        except RuntimeError as e:
            print("ERROR: %s" % e)
            return FAIL_EXIT
        if not unblocks and not sweep:
            print("%s: nothing actionable." % JOB)
            return 0
        with open(round_path(), "w", encoding="utf-8") as f:
            json.dump({"attempt": 1, "unblocks": unblocks,
                       "sweep": sweep}, f)
        return emit_request(build_task(unblocks, sweep), RESULT_SCHEMA, 1)

    try:
        with open(round_path(), encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        print("ERROR: no round state; cannot match an agent result.")
        return FAIL_EXIT
    attempt = state.get("attempt", 1)

    try:
        result = json.loads(args.agent_result)
        err = validate_result(result)
    except ValueError as e:
        err = "result is not valid JSON: %s" % e

    if err:
        if attempt >= MAX_ROUNDS:
            print("agent result invalid after %d rounds (%s); failing "
                  "loudly." % (MAX_ROUNDS, err))
            return FAIL_EXIT
        state["attempt"] = attempt + 1
        with open(round_path(), "w", encoding="utf-8") as f:
            json.dump(state, f)
        return emit_request("Your last result was invalid (%s). Try again:"
                            "\n\n%s" % (err, build_task(
                                state["unblocks"], state["sweep"])),
                            RESULT_SCHEMA, attempt + 1)

    try:
        os.remove(round_path())
    except OSError:
        pass
    try:
        marked = run_watch(["--mark-handled",
                            json.dumps(result["handled"])])
    except RuntimeError as e:
        print("ERROR: %s" % e)
        return FAIL_EXIT
    lines = ["%s digest: %d acted, %d handled, %d error(s)."
             % (JOB, len(result["acted"]), len(result["handled"]),
                len(result["errors"]))]
    for a in result["acted"]:
        lines.append("- %s: %s (%s)" % (a["id"], a["action"], a["note"]))
    for e in result["errors"]:
        lines.append("- ERROR: %s" % e)
    lines.append("handled ids now recorded: %d" %
                 len(marked.get("handled", [])))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
