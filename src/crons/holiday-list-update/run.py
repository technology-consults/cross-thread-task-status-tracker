#!/usr/bin/env python3
"""holiday-list-update — versioned package entrypoint (run.py).

Behavior-preserving move of the cron body previously executed by the agent
(quarterly, 1st of Jan/Apr/Jul/Oct, 20:00 America/Toronto):

1. (script) compute the window: the next four calendar months starting with
   the current month (Toronto date).
2. (agent, handshake) fetch the official NYSE holiday calendar press release
   and the Nasdaq-published copy covering the window; extract every FULL-DAY
   market closure inside the window (ignore early-close days).
3. (script) validate + cross-check: both sources must agree on every date.
   - Disagreement -> print the flag message, exit 0 (defined outcome; the
     thin body delivers it to the job's chat target).
   - Agreement -> write the canonical JSON, run the vendored
     sync_holiday_copies.py (validates + mirrors to the repo via API).
     Sync failure -> brief message, exit 0. Success -> silent one-liner.

The canonical JSON is written to the authoritative local copy, then mirrored
one-way to holidays/nyse_holidays.json in the tracker repo. This job is the
ONLY writer of the shared holiday list.
"""
import argparse
import calendar
import json
import os
import subprocess
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = "holiday-list-update"
TZ = ZoneInfo("America/Toronto")

REQ_BEGIN = "@@AGENT-REQUEST-BEGIN@@"
REQ_END = "@@AGENT-REQUEST-END@@"
HANDSHAKE_EXIT = 10
FAIL_EXIT = 20
MAX_ROUNDS = 5

NYSE_URL = ("https://ir.theice.com/press/news-details/2025/"
            "NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-"
            "Closings-Calendar/default.aspx")
NASDAQ_URL = ("https://www.nasdaq.com/press-release/nyse-group-announces-"
              "2025-2026-and-2027-holiday-and-early-closings-calendar-2024-11")

CALENDAR_SCHEMA = {
    "type": "object",
    "properties": {
        "holidays": {"type": "array", "items": {"type": "string"}},
        "nyse_url": {"type": "string"},
        "nasdaq_url": {"type": "string"},
        "disagreement": {"type": "object"},
    },
    "required": ["holidays", "nyse_url", "nasdaq_url"],
}


def canonical_path():
    override = os.environ.get("CRON_HOLIDAYS_JSON")
    if override:
        return override
    return os.path.join(os.path.expanduser("~"), "workspace", "shared",
                        "holidays", "nyse_holidays.json")


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


def window(today):
    """(start, end) date objects: first of this month .. last of month+3."""
    start = today.replace(day=1)
    y, m = start.year, start.month + 3
    while m > 12:
        y += 1
        m -= 12
    end = date(y, m, calendar.monthrange(y, m)[1])
    return start, end


def valid_ymd(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def validate_result(result, schema):
    if not isinstance(result, dict):
        return "result is not a JSON object"
    for key in schema.get("required", ()):
        if key not in result:
            return "missing required key %r" % key
    return None


def emit_request(task, schema, attempt):
    print(REQ_BEGIN)
    print(json.dumps({"need": "agent-step", "task": task,
                      "schema": schema, "attempt": attempt}, indent=2))
    print(REQ_END)
    return HANDSHAKE_EXIT


def build_calendar_task(start, end):
    months = []
    y, m = start.year, start.month
    for _ in range(4):
        months.append("%s %d" % (calendar.month_name[m], y))
        m += 1
        if m > 12:
            y += 1
            m = 1
    return "\n".join([
        "NYSE/Nasdaq holiday calendar fetch for the window %s to %s "
        "(%s)." % (start.isoformat(), end.isoformat(), ", ".join(months)),
        "",
        "1. Fetch the official NYSE holiday calendar press release:",
        "   " + NYSE_URL,
        "2. Fetch the Nasdaq-published copy of the same NYSE calendar:",
        "   " + NASDAQ_URL,
        "   If the Nasdaq copy does not cover the full window, find the "
        "current Nasdaq publication of the NYSE holiday calendar that does "
        "(same press-release series) and use that instead. Never cross-check "
        "against a source that does not cover the window.",
        "3. Extract every FULL-DAY market closure (YYYY-MM-DD) inside the "
        "window - ignore early-close days, ignore anything outside it.",
        "4. Cross-check: both sources must agree on every date in the window.",
        "",
        "Reply with JSON matching the schema:",
        '{"holidays": ["YYYY-MM-DD", ...], "nyse_url": "<url used>", '
        '"nasdaq_url": "<url used>", "disagreement": null}',
        "If the sources disagree on any date, set holidays to [] and "
        "disagreement to {\"date\": \"YYYY-MM-DD\", \"nyse_says\": \"...\", "
        "\"nasdaq_says\": \"...\"}. Do NOT guess and do NOT invent dates.",
    ])


def build_canonical(today, start, end, holidays, nyse_url, nasdaq_url):
    months = []
    y, m = start.year, start.month
    for _ in range(4):
        months.append("%s %d" % (calendar.month_abbr[m], y))
        m += 1
        if m > 12:
            y += 1
            m = 1
    return {
        "updated": today.isoformat(),
        "sources": [nyse_url, nasdaq_url],
        "note": ("Full-day NYSE closures (YYYY-MM-DD) for the next four "
                 "calendar months (%s-%s). Single source of truth, "
                 "maintained ONLY by the holiday-list-update cron "
                 "(quarterly, 1st of Jan/Apr/Jul/Oct)."
                 % (months[0], months[-1])),
        "holidays": sorted(holidays),
    }


def run_sync_script(path):
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "sync_holiday_copies.py"), path],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        timeout=600)
    return proc.returncode, proc.stdout or ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent-result", default=None)
    args = ap.parse_args(argv)
    today = datetime.now(TZ).date()

    if args.agent_result is None:
        start, end = window(today)
        with open(round_state_path(), "w", encoding="utf-8") as f:
            json.dump({"start": start.isoformat(), "end": end.isoformat(),
                       "attempt": 1}, f)
        return emit_request(build_calendar_task(start, end),
                            CALENDAR_SCHEMA, 1)

    try:
        with open(round_state_path(), encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        print("ERROR: no round state; cannot match an agent result.")
        return FAIL_EXIT
    attempt = state.get("attempt", 1)
    start = date.fromisoformat(state["start"])
    end = date.fromisoformat(state["end"])

    try:
        result = json.loads(args.agent_result)
        err = validate_result(result, CALENDAR_SCHEMA)
    except ValueError as e:
        err = "result is not valid JSON: %s" % e
    if err:
        if attempt >= MAX_ROUNDS:
            print("agent result invalid after %d rounds (%s); failing "
                  "loudly." % (MAX_ROUNDS, err))
            return FAIL_EXIT
        with open(round_state_path(), "w", encoding="utf-8") as f:
            json.dump({"start": state["start"], "end": state["end"],
                       "attempt": attempt + 1}, f)
        task = ("Your last result was invalid (%s). Try again:\n\n" % err
                + build_calendar_task(start, end))
        return emit_request(task, CALENDAR_SCHEMA, attempt + 1)

    disagreement = result.get("disagreement")
    if disagreement:
        print("Holiday sources DISAGREE on %s: NYSE says %s; Nasdaq says "
              "%s. Not writing anything - needs a human look."
              % (disagreement.get("date"), disagreement.get("nyse_says"),
                 disagreement.get("nasdaq_says")))
        return 0

    holidays = result.get("holidays") or []
    bad = [d for d in holidays if not valid_ymd(d)]
    out_of_window = [d for d in holidays
                     if valid_ymd(d) and not (start.isoformat() <= d
                                              <= end.isoformat())]
    if bad or out_of_window:
        print("Agent returned unusable dates (bad=%r, out_of_window=%r); "
              "not writing anything - needs a human look."
              % (bad[:5], out_of_window[:5]))
        return 0

    doc = build_canonical(today, start, end, holidays,
                          result["nyse_url"], result["nasdaq_url"])
    path = canonical_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")

    rc, out = run_sync_script(path)
    try:
        os.remove(round_state_path())
    except OSError:
        pass
    if rc != 0:
        print("Holiday list written locally, but the repo mirror sync "
              "FAILED:\n%s" % out.strip())
        return 0
    print("silent: holiday list refreshed for %s-%s (%d closures, updated "
          "%s); no user message per job definition."
          % (start.isoformat(), end.isoformat(), len(holidays),
             today.isoformat()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
