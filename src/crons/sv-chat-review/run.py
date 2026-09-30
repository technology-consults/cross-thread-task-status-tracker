#!/usr/bin/env python3
"""sv-chat-review — versioned package entrypoint (run.py).

Behavior-preserving move of the cron body previously executed by the agent
(twice daily ~06:00 and ~12:00 America/Toronto; runs 06:00-12:00 and
12:00-24:00 windows). Extracts proposals, decisions, agreements, gates and
tasks from the SV tracker thread and files them in the right places.

Track B: script-as-orchestrator, two agent rounds.
- Script-driven: watermark storage (seeded once from the goal hidden_files
  chat_review_state.json), result validation, and the digest.
- Agent-driven (handshake): round 1 extracts items from the thread since
  the watermark (reading chat history is agent work); round 2 files them
  (GitHub API doc updates, board task creation, program.json updates,
  reversible autonomous implementation) applying the autonomy rules.

Handshake: script exits 10 with @@AGENT-REQUEST-BEGIN@@ JSON {need, task,
schema, attempt}; the agent returns the round's JSON; the script validates.
Max 5 rounds per request, then exit 20 (fail loudly, never partial).
"""
import argparse
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

JOB = "sv-chat-review"
TZ = ZoneInfo("America/Toronto")
SV_TRACKER_ID = "d82796e3-56f1-4d34-bf51-665165a38e92"
FOR_REVIEW_THREAD = "b95fb15f-a58f-4547-b9cd-cdce882a5cd9"
GOAL_HIDDEN = "short-video-creation-and-publishing-pipeline"
SEED_FILE = "chat_review_state.json"

REQ_BEGIN = "@@AGENT-REQUEST-BEGIN@@"
REQ_END = "@@AGENT-REQUEST-END@@"
HANDSHAKE_EXIT = 10
FAIL_EXIT = 20
MAX_ROUNDS = 5

ITEM_TYPES = {"proposal", "decision", "agreement", "gate", "task"}

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {"type": "array", "items": {"type": "object"}},
        "last_seen_message_id": {"type": "string"},
    },
    "required": ["items", "last_seen_message_id"],
}
FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "filed": {"type": "array", "items": {"type": "object"}},
        "errors": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["filed", "errors"],
}


def home():
    return os.path.expanduser("~")


def state_dir():
    override = os.environ.get("CRON_JOB_STATE_DIR")
    if override:
        os.makedirs(override, exist_ok=True)
        return override
    d = os.path.join(home(), ".cron_runner", "job_state", JOB)
    os.makedirs(d, exist_ok=True)
    return d


def watermarks_path():
    return os.path.join(state_dir(), "watermarks.json")


def goal_hidden_dir():
    return os.path.join(home(), "workspace", "goals", GOAL_HIDDEN,
                        "hidden_files")


def seed_watermark():
    """First run: pick up the SV watermark from the goal hidden files."""
    seed = os.path.join(goal_hidden_dir(), SEED_FILE)
    try:
        with open(seed, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    chats = data.get("chats", {}) if isinstance(data, dict) else {}
    for key in (SV_TRACKER_ID, "sv"):
        if key in chats and isinstance(chats[key], dict):
            return chats[key].get("watermark")
    return None


def load_watermarks():
    p = watermarks_path()
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        wm = {"sv": seed_watermark(), "updated": None}
        save_watermarks(wm)
        return wm


def save_watermarks(wm):
    wm["updated"] = datetime.now(TZ).isoformat()
    with open(watermarks_path(), "w", encoding="utf-8") as f:
        json.dump(wm, f, indent=2)


def round_path():
    return os.path.join(state_dir(), "round.json")


def emit_request(task, schema, attempt):
    print(REQ_BEGIN)
    print(json.dumps({"need": "agent-step", "task": task,
                      "schema": schema, "attempt": attempt}, indent=2))
    print(REQ_END)
    return HANDSHAKE_EXIT


def validate_extract(result):
    if not isinstance(result, dict):
        return "result is not a JSON object"
    if not isinstance(result.get("items"), list):
        return "missing required key 'items' (array)"
    if not isinstance(result.get("last_seen_message_id"), str):
        return "missing required key 'last_seen_message_id' (string)"
    for i, item in enumerate(result["items"]):
        if not isinstance(item, dict):
            return "items[%d] is not an object" % i
        if item.get("type") not in ITEM_TYPES:
            return ("items[%d].type must be one of %s"
                    % (i, sorted(ITEM_TYPES)))
        if not isinstance(item.get("summary"), str):
            return "items[%d].summary must be a string" % i
    return None


def validate_filed(result):
    if not isinstance(result, dict):
        return "result is not a JSON object"
    if not isinstance(result.get("filed"), list):
        return "missing required key 'filed' (array)"
    if not isinstance(result.get("errors"), list):
        return "missing required key 'errors' (array)"
    for i, f in enumerate(result["filed"]):
        if not isinstance(f, dict):
            return "filed[%d] is not an object" % i
        for k in ("summary", "action", "detail"):
            if not isinstance(f.get(k), str):
                return "filed[%d].%s must be a string" % (i, k)
    return None


def build_extract_task(watermark):
    since = ("messages after %s" % watermark) if watermark else \
        "today's new messages (no prior watermark; first review)"
    return "\n".join([
        "SV chat review: extraction round.",
        "Read the SV tracker thread (ID %s). Consider only %s." %
        (SV_TRACKER_ID, since),
        "Extract every proposal, decision, agreement, gate, and task you "
        "find in that window. Classify each item's type as one of: "
        "proposal, decision, agreement, gate, task.",
        'Reply with JSON: {"items": [{"type": "<one of the five>", '
        '"summary": "<plain-words summary>", "detail": "<context needed '
        'to file it>"}], "last_seen_message_id": "<newest message id you '
        'read>"}.',
        "If nothing new, return an empty items array.",
    ])


def build_file_task(items):
    return "\n".join([
        "SV chat review: filing round. File each extracted item per the "
        "rules below, then reply with JSON.",
        "Extracted items:",
        json.dumps(items, indent=2),
        "",
        "Filing rules:",
        "- proposal: research it and decide yourself, then handle it like "
        "a decision.",
        "- decision / agreement: if it is docs material, update or add the "
        "doc in the owning repo via the GitHub API; if it is actionable "
        "work, create a board task titled '[DECISION] ...'. Then record it "
        "into program.json.",
        "- gate: update the doc section, create a review task with a poke, "
        "and post the summary to BOTH the SV tracker thread and the For "
        "review thread (ID %s)." % FOR_REVIEW_THREAD,
        "- task: if it builds something, create a board task '[BUILD]'; "
        "if it only reviews or approves, create '[REVIEW]'; if it is "
        "autonomous, implement it reversibly, summarize, and mark done.",
        "- Never do work that needs credentials, secrets, or auth flows — "
        "create a task asking him instead.",
        "- Never touch repos whose owners are not his — if unsure, create "
        "a review task.",
        "- Ambiguous task text: research, pick the best interpretation, "
        "record it.",
        'Reply with JSON: {"filed": [{"summary": "<item>", "action": '
        '"<what you did>", "detail": "<where it landed>"}], "errors": '
        '["<anything you could not file and why>"]}.',
    ])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-result", default=None)
    args = ap.parse_args(argv)
    wm = load_watermarks()

    if args.agent_result is None:
        with open(round_path(), "w", encoding="utf-8") as f:
            json.dump({"phase": "extract", "attempt": 1}, f)
        return emit_request(build_extract_task(wm.get("sv")),
                            EXTRACT_SCHEMA, 1)

    try:
        with open(round_path(), encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        print("ERROR: no round state; cannot match an agent result.")
        return FAIL_EXIT
    phase = state.get("phase", "extract")
    attempt = state.get("attempt", 1)

    try:
        result = json.loads(args.agent_result)
        err = (validate_extract if phase == "extract"
               else validate_filed)(result)
    except ValueError as e:
        err = "result is not valid JSON: %s" % e

    if err:
        if attempt >= MAX_ROUNDS:
            print("agent result invalid after %d rounds (%s); failing "
                  "loudly." % (MAX_ROUNDS, err))
            return FAIL_EXIT
        task = (build_extract_task(wm.get("sv")) if phase == "extract"
                else build_file_task(state.get("items", [])))
        schema = EXTRACT_SCHEMA if phase == "extract" else FILE_SCHEMA
        state["attempt"] = attempt + 1
        with open(round_path(), "w", encoding="utf-8") as f:
            json.dump(state, f)
        return emit_request("Your last result was invalid (%s). Try again:"
                            "\n\n%s" % (err, task), schema, attempt + 1)

    if phase == "extract":
        items = result["items"]
        last_seen = result["last_seen_message_id"]
        if not items:
            wm["sv"] = last_seen
            save_watermarks(wm)
            try:
                os.remove(round_path())
            except OSError:
                pass
            print("SV chat review: nothing new since %s." %
                  (wm.get("sv") or "first review"))
            return 0
        with open(round_path(), "w", encoding="utf-8") as f:
            json.dump({"phase": "file", "attempt": 1, "items": items,
                       "last_seen": last_seen}, f)
        return emit_request(build_file_task(items), FILE_SCHEMA, 1)

    # phase == "file"
    filed = result["filed"]
    errors = result["errors"]
    wm["sv"] = state.get("last_seen", wm.get("sv"))
    save_watermarks(wm)
    try:
        os.remove(round_path())
    except OSError:
        pass
    counts = {}
    for f in filed:
        counts[f["action"]] = counts.get(f["action"], 0) + 1
    lines = ["SV chat review digest: %d extracted, %d filed, %d error(s)."
             % (len(state.get("items", [])), len(filed), len(errors))]
    for action, n in sorted(counts.items()):
        lines.append("- %d x %s" % (n, action))
    for f in filed:
        lines.append("- filed: %s -> %s (%s)" %
                     (f["summary"], f["action"], f["detail"]))
    for e in errors:
        lines.append("- ERROR: %s" % e)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
