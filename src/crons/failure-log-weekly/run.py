#!/usr/bin/env python3
"""failure-log-weekly — versioned package entrypoint (run.py).

Behavior-preserving move of the cron body previously executed by the agent
(weekly Monday 08:00 America/Toronto). Reports the last 7 days of entries
from verifier/failures.md in this repo to the failure-log side chat.

Track B: script-as-orchestrator.
- Script-driven: everything. Fetching the file, parsing entries, filtering
  the 7-day window, and composing the report are all deterministic — no
  agent step exists for this job, so there is no handshake (exit 10 never
  fires).

Rules from the definition:
- File missing -> graceful message, exit 0, NO chat delivery needed.
- Entries in window -> deliver the report to the failure log side chat
  (ID de5d7ab8-9709-4e7c-a556-fd5f582b2f7e) as a failure-log-weekly message.
- No entries in window -> deliver an explicit no-new-failures report.

Entry format: numbered lines under the `## Entries (newest last)` heading,
each like `1. 2026-09-24 — <description>`.
"""
import os
import re
import sys
from datetime import date, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from github_api import get_contents, GitHubError  # noqa: E402

JOB = "failure-log-weekly"
REPO = "technology-consults/cross-thread-task-status-tracker"
FAILURES_PATH = "verifier/failures.md"
TZ = ZoneInfo("America/Toronto")

ENTRY_RE = re.compile(
    r"^\s*(\d+)\.\s+(\d{4})-(\d{2})-(\d{2})\s*[-\u2013\u2014]\s*(.*)$")


def today():
    from datetime import datetime
    return datetime.now(TZ).date()


def fetch_failures():
    """Return file text, or None if it does not exist."""
    try:
        text, _ = get_contents(REPO, FAILURES_PATH)
        return text
    except GitHubError:
        return None


def parse_entries(text):
    """Parse (date, description) entries from the Entries section.

    Returns (entries, unparsed_lines). Only lines under a `## Entries`
    heading are considered; parsing stops at the next `## ` heading.
    """
    entries = []
    unparsed = []
    in_entries = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_entries = stripped[3:].lower().startswith("entries")
            continue
        if not in_entries or not stripped:
            continue
        m = ENTRY_RE.match(line)
        if m:
            try:
                d = date(int(m.group(2)), int(m.group(3)), int(m.group(4)))
            except ValueError:
                unparsed.append(line)
                continue
            entries.append((d, m.group(5).strip()))
        elif re.match(r"^\s*\d+\.\s", line):
            unparsed.append(line)
    return entries, unparsed


def window(today):
    return today - timedelta(days=6), today


def main(argv=None):
    now = today()
    text = fetch_failures()
    if text is None:
        print("note: %s not found in %s — nothing to report; "
              "skipping this week (no chat delivery needed)." %
              (FAILURES_PATH, REPO))
        return 0
    entries, unparsed = parse_entries(text)
    start, end = window(now)
    recent = [(d, desc) for d, desc in entries
              if start <= d <= end]
    recent.sort(key=lambda e: e[0], reverse=True)
    if not recent:
        print("failure-log-weekly report (week ending %s): no new failures "
              "in the last 7 days." % end.isoformat())
    else:
        lines = ["failure-log-weekly report (week ending %s): %d new "
                 "failure(s)" % (end.isoformat(), len(recent))]
        for i, (d, desc) in enumerate(recent, 1):
            lines.append("%d. %s \u2014 %s" % (i, d.isoformat(), desc))
        print("\n".join(lines))
    if unparsed:
        print("note: %d line(s) under ## Entries could not be parsed and "
              "were skipped." % len(unparsed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
