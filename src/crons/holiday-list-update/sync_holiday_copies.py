#!/usr/bin/env python3
"""Sync the canonical NYSE holiday list to its versioned git mirror.

VENDORED COPY. Source: scripts/sync_holiday_copies.py in
technology-consults/cross-thread-task-status-tracker (vendored 2026-09-30).
Adaptation for the versioned-cron package (behavior-preserving):
- DEFAULT_JSON via CRON_HOLIDAYS_JSON env override, else the canonical
  holiday file under the runtime user's home (constructed without
  literals, per CRON-001).
- Prose mentioning the on-disk layout reworded; no behavior change.

Target (GitHub API only -- never git CLI, never browser):
  technology-consults/cross-thread-task-status-tracker
  holidays/nyse_holidays.json @ main      -- versioned mirror

This script NEVER touches the trading portal. The portal deployable is
assembled separately by the portal deploy script, which reads this same
JSON from the cross-thread repo at deploy time.

Usage:
    python3 sync_holiday_copies.py [path-to-json] [--dry-run]

--dry-run validates the JSON and prints what would be pushed, making no
API calls and changing nothing.

Exit codes: 0 on success, 1 on validation or push failure.
"""

import argparse
import base64
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_JSON = os.environ.get("CRON_HOLIDAYS_JSON") or os.path.join(
    os.path.expanduser("~"), "workspace", "shared", "holidays",
    "nyse_holidays.json")

MIRROR_REPO = "technology-consults/cross-thread-task-status-tracker"
MIRROR_PATH = "holidays/nyse_holidays.json"
MIRROR_BRANCH = "main"

REQUIRED_KEYS = ("updated", "sources", "note", "holidays")


class GitHubError(RuntimeError):
    """GitHub API failure, carrying the HTTP status code."""

    def __init__(self, method, path, code, body):
        super().__init__(f"GitHub {method} {path}: HTTP {code} {body[:200]}")
        self.code = code


def api(method, path, payload=None):
    """One GitHub API call, authenticated via the custom.github surrogate."""
    sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
    from dynamic_credentials import add_surrogate_to_request

    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        "https://api.github.com" + path, data=data, method=method,
        headers={"User-Agent": "muse-agent",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    add_surrogate_to_request(req, "custom.github",
                             allowed_hosts=["api.github.com"])
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
            return json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as e:
        raise GitHubError(method, path, e.code, e.read().decode())


def valid_ymd(s):
    """True if s is a real calendar date in YYYY-MM-DD form."""
    try:
        datetime.datetime.strptime(s, "%Y-%m-%d")
        return True
    except (TypeError, ValueError):
        return False


def load_and_validate(path):
    """Load the JSON file and validate its shape.

    Returns (text, data). Raises ValueError with a plain-words message
    on any problem.
    """
    if not os.path.isfile(path):
        raise ValueError(f"holiday file not found: {path}")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"not valid JSON: {e}")

    if not isinstance(data, dict):
        raise ValueError("top-level JSON must be an object, "
                         f"got {type(data).__name__}")
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"missing required keys: {', '.join(missing)}")

    if not isinstance(data["updated"], str) or not valid_ymd(data["updated"]):
        raise ValueError(
            '"updated" must be a YYYY-MM-DD date string, '
            f"got: {data['updated']!r}")

    if not isinstance(data["sources"], list) or not all(
            isinstance(s, str) for s in data["sources"]):
        raise ValueError('"sources" must be a list of strings')

    if not isinstance(data["note"], str):
        raise ValueError('"note" must be a string')

    holidays = data["holidays"]
    if not isinstance(holidays, list) or not holidays:
        raise ValueError('"holidays" must be a non-empty list of YYYY-MM-DD '
                         "date strings")
    bad = [d for d in holidays
           if not isinstance(d, str) or not valid_ymd(d)]
    if bad:
        raise ValueError(
            '"holidays" contains invalid YYYY-MM-DD dates: '
            f"{bad[:5]!r}")
    seen, dupes = set(), set()
    for d in holidays:
        if d in seen:
            dupes.add(d)
        seen.add(d)
    if dupes:
        raise ValueError(
            f'"holidays" contains duplicate dates: {sorted(dupes)!r}')
    if list(holidays) != sorted(holidays):
        raise ValueError('"holidays" must be sorted ascending (YYYY-MM-DD)')

    return text, data


def push_file(repo, path, branch, text, message):
    """PUT text to repo/path@branch via the contents API.

    Creates the file when it does not exist yet; skips the push when the
    content is identical to what is already there. Returns a human-readable
    result line for printing.
    """
    cur = None
    try:
        cur = api("GET", f"/repos/{repo}/contents/{path}?ref={branch}")
    except GitHubError as e:
        if e.code != 404:
            raise
        # File does not exist yet -> create it below (no sha).

    if cur is not None:
        try:
            existing = base64.b64decode(cur.get("content", "")).decode("utf-8")
        except Exception:
            existing = None
        if existing == text:
            return (f"unchanged: {repo} {path}@{branch} "
                    f"-> blob {cur['sha'][:7]} (content identical, no commit)")

    payload = {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode(),
        "branch": branch,
    }
    if cur is not None:
        payload["sha"] = cur["sha"]
    r = api("PUT", f"/repos/{repo}/contents/{path}", payload)
    return (f"pushed: {repo} {path}@{branch} "
            f"-> commit {r['commit']['sha'][:7]}")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Sync the canonical holiday JSON to its git copies.")
    ap.add_argument("json_path", nargs="?", default=DEFAULT_JSON,
                    help="path to the holiday JSON "
                         f"(default: {DEFAULT_JSON})")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate only; print what would be pushed, "
                         "make no API calls")
    args = ap.parse_args(argv)

    try:
        text, data = load_and_validate(args.json_path)
    except (ValueError, OSError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    n = len(data["holidays"])
    span = f"{data['holidays'][0]} .. {data['holidays'][-1]}"
    print(f"validated: {args.json_path} "
          f"({n} holidays, {span}, updated {data['updated']})")

    if args.dry_run:
        print(f"DRY RUN: would push {MIRROR_REPO} "
              f"{MIRROR_PATH}@{MIRROR_BRANCH}")
        print(f'         message: "holiday list: update from '
              f'{data["updated"]}"')
        print("DRY RUN: no API calls made, nothing changed")
        return 0

    try:
        # Versioned mirror: must succeed, or we exit non-zero.
        print(push_file(MIRROR_REPO, MIRROR_PATH, MIRROR_BRANCH, text,
                        f"holiday list: update from {data['updated']}"))
    except GitHubError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
