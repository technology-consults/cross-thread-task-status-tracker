#!/usr/bin/env python3
"""job-watchdog — versioned package entrypoint (run.py).

Behavior-preserving move of the cron body previously executed by the agent
(daily 06:00 America/Toronto). Checks the health of the fixed watch list of
recurring scheduled jobs and reports ONLY problems; stays silent when all
are healthy.

Track B: script-as-orchestrator.
- Script-driven: the fixed watch list, missed-run windows, the NYSE
  trading-day extension, and the healthy/missed/failed decision rules.
- Agent-driven (handshake): reading cron.status (enabled?) and cron.runs
  (recent runs: time, status, error text) for each watched job — these are
  agent-only tools, so the agent is the callable service for that step.

Handshake: exit 10 with @@AGENT-REQUEST-BEGIN@@ JSON {need, task, schema,
attempt}; the agent returns per-job run data; the script validates and
decides. Max 5 rounds, then exit 20 (fail loudly, never partial).

Detection and reporting only: never fixes anything, never modifies a
schedule. Notable observations go to the daily log.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from github_api import get_contents  # noqa: E402

JOB = "job-watchdog"
REPO = "technology-consults/cross-thread-task-status-tracker"
TZ = ZoneInfo("America/Toronto")

REQ_BEGIN = "@@AGENT-REQUEST-BEGIN@@"
REQ_END = "@@AGENT-REQUEST-END@@"
HANDSHAKE_EXIT = 10
FAIL_EXIT = 20
MAX_ROUNDS = 5

# Fixed watch list: (job_id, window_hours, etf). etf=True jobs get the
# weekend/market-holiday window extension to 72h (jobs 1-4, 6, 8, 12).
WATCH = [
    ("etf-live-bundle", None, True),      # special: active-hours logic
    ("etf-signal-intraday-market", 3, True),
    ("etf-price-updates", 3, True),
    ("etf-signal-intraday-offhours", 8, True),
    ("repo-pull", 30, False),
    ("etf-trading-signals", 30, True),
    ("phev-ev-suv-deal-watch", 30, False),
    ("signal-scorecard", 30, True),
    ("phev-ev-suv-payment-watch", 30, False),
    ("cron-definitions-sync", 30, False),
    ("task-due-date-watch", 30, False),
    ("etf-price-preclose", 30, True),
    ("etf-cron-timing-tuner", 8 * 24, False),
    ("etf-signal-engine-review", 8 * 24, False),
    ("holiday-list-update", 100 * 24, False),
]
WATCH_IDS = [j for j, _, _ in WATCH]

RUNS_SCHEMA = {
    "type": "object",
    "properties": {
        "jobs": {"type": "array", "items": {"type": "object"}},
    },
    "required": ["jobs"],
}

FAILED_STATUSES = {"failed", "error"}


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


def parse_time(s):
    try:
        dt = datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def market_holidays():
    """Set of YYYY-MM-DD full-day closures from the repo's holiday list.

    Falls back to empty (weekend-only logic) if the fetch fails; the
    caller notes the fallback in its output.
    """
    try:
        text, _ = get_contents(REPO, "holidays/nyse_holidays.json")
        return set(json.loads(text).get("holidays", []))
    except Exception:
        return None


def is_trading_day(today, holidays):
    if today.weekday() >= 5:  # Sat/Sun
        return False
    if holidays and today.isoformat() in holidays:
        return False
    return True


def live_bundle_active(now):
    """etf-live-bundle active window: weekdays 04:00-21:00 ET."""
    return now.weekday() < 5 and 4 <= now.hour < 21


def effective_window(job_id, base_hours, etf, now, trading_day):
    if job_id == "etf-live-bundle":
        if live_bundle_active(now) and trading_day:
            return 0.5
        return 72.0
    if etf and not trading_day:
        return 72.0
    return float(base_hours)


def validate_result(result):
    if not isinstance(result, dict):
        return "result is not a JSON object"
    if "jobs" not in result or not isinstance(result["jobs"], list):
        return "missing required key 'jobs' (array)"
    for entry in result["jobs"]:
        if not isinstance(entry, dict) or "id" not in entry:
            return "each jobs[] entry must be an object with an 'id'"
        if "enabled" in entry and not isinstance(entry["enabled"], bool):
            return "'enabled' must be a boolean for %r" % entry.get("id")
        for r in entry.get("runs", []):
            if not isinstance(r, dict) or "at" not in r or "status" not in r:
                return "each runs[] entry needs 'at' and 'status'"
    return None


def emit_request(task, schema, attempt):
    print(REQ_BEGIN)
    print(json.dumps({"need": "agent-step", "task": task,
                      "schema": schema, "attempt": attempt}, indent=2))
    print(REQ_END)
    return HANDSHAKE_EXIT


def build_runs_task():
    return "\n".join([
        "Scheduled-job run data collection for the watchdog.",
        "For EACH job id below, use cron.status to check whether it is "
        "currently enabled, and cron.runs to fetch its most recent runs "
        "(up to 5: time, status, error text).",
        "Jobs: " + ", ".join(WATCH_IDS),
        'Reply with JSON: {"jobs": [{"id": "<job>", "enabled": true/false, '
        '"runs": [{"at": "<ISO 8601 with timezone>", "status": '
        '"<completed|failed|error|...>", "error": "<text or null>"}]}]}.',
        "Include every job id exactly once, even if it has no runs "
        '(use "runs": []). Do not add any other jobs.',
    ])


def evaluate(now, holidays_note_ok, holidays, runs_by_id):
    """Apply the fixed rules. Return (problems, notes)."""
    problems = []
    notes = []
    if not holidays_note_ok:
        notes.append("holiday list unavailable; using weekend-only "
                     "trading-day logic")
    today = now.date()
    trading_day = is_trading_day(today, holidays or set())
    for job_id, base_hours, etf in WATCH:
        entry = runs_by_id.get(job_id)
        if entry is None:
            problems.append((job_id, "no run data returned by the agent",
                             "needs attention"))
            continue
        if not entry.get("enabled", True):
            continue  # disabled is intentional, not a problem
        runs = entry.get("runs", [])
        if runs and runs[0].get("status") in FAILED_STATUSES:
            problems.append(
                (job_id, "latest run FAILED at %s: %s"
                 % (runs[0].get("at"), runs[0].get("error") or "no error "
                    "text"), "needs attention"))
        window_h = effective_window(job_id, base_hours, etf, now,
                                    trading_day)
        cutoff = now - timedelta(hours=window_h)
        healthy = any(r.get("status") == "completed"
                      and (t := parse_time(r.get("at"))) is not None
                      and t >= cutoff for r in runs)
        if not healthy:
            if job_id == "etf-live-bundle" and not live_bundle_active(now):
                what = "no runs in 3 days (outside active hours)"
            else:
                if window_h < 1:
                    what = "no completed run within %d min" % round(
                        window_h * 60)
                elif window_h < 72:
                    what = "no completed run within %.0f h" % window_h
                else:
                    what = "no completed run within 3 days"
                if etf and not trading_day:
                    what += " (non-trading day: window extended to 3 days)"
            last = runs[0].get("at") if runs else "never"
            problems.append((job_id, "missed run: %s; last run: %s"
                             % (what, last), "transient unless it repeats"))
    return problems, notes


def append_daily_log(today, line):
    mem_dir = os.environ.get("CRON_MEMORY_DIR") or os.path.join(
        os.path.expanduser("~"), "memory")
    os.makedirs(mem_dir, exist_ok=True)
    with open(os.path.join(mem_dir, "%s.md" % today), "a",
              encoding="utf-8") as f:
        f.write("\n- %s\n" % line)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-result", default=None)
    args = ap.parse_args(argv)
    now = datetime.now(TZ)

    if args.agent_result is None:
        holidays = market_holidays()
        with open(round_state_path(), "w", encoding="utf-8") as f:
            json.dump({"holidays_ok": holidays is not None,
                       "holidays": sorted(holidays or []),
                       "attempt": 1}, f)
        return emit_request(build_runs_task(), RUNS_SCHEMA, 1)

    try:
        with open(round_state_path(), encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        print("ERROR: no round state; cannot match an agent result.")
        return FAIL_EXIT
    attempt = state.get("attempt", 1)
    holidays = set(state.get("holidays", []))
    holidays_ok = state.get("holidays_ok", False)

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
        with open(round_state_path(), "w", encoding="utf-8") as f:
            json.dump({"holidays_ok": holidays_ok,
                       "holidays": sorted(holidays),
                       "attempt": attempt + 1}, f)
        return emit_request("Your last result was invalid (%s). Try again:\n\n"
                            % err + build_runs_task(),
                            RUNS_SCHEMA, attempt + 1)

    try:
        os.remove(round_state_path())
    except OSError:
        pass
    runs_by_id = {e["id"]: e for e in result["jobs"]}
    problems, notes = evaluate(now, holidays_ok, holidays, runs_by_id)
    for n in notes:
        print("note: %s" % n)
    if not problems:
        print("Watchdog: all scheduled jobs healthy.")
        return 0
    lines = ["Watchdog found %d problem(s):" % len(problems)]
    for job_id, what, verdict in problems:
        lines.append("- %s: %s [%s]" % (job_id, what, verdict))
    report = "\n".join(lines)
    print(report)
    append_daily_log(now.date().isoformat(), "job-watchdog: " +
                     "; ".join("%s: %s" % (j, w) for j, w, _ in problems))
    return 0


if __name__ == "__main__":
    sys.exit(main())
