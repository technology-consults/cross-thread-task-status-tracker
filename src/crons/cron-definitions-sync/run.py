#!/usr/bin/env python3
"""cron-definitions-sync — versioned package entrypoint (run.py).

Behavior-preserving move of the cron body previously executed by the agent:
runs the vendored sync logic (scheduler's saved definitions -> git mirror
+ review page), committing via the GitHub API only when something changed.

Reply contract (this script's stdout is the run's result):
  - no change:  "no changes."
  - committed:   "<commit-sha> <n> files changed"
  - error:       brief error text on stdout, exit non-zero.

Deterministic job: no agent handshake (no exit 10 path).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SYNC_SCRIPT = os.path.join(HERE, "sync_crons_to_git.py")


def run_sync():
    """Run the vendored sync; return (sha_or_None, n_files, raw_output)."""
    proc = subprocess.run(
        [sys.executable, SYNC_SCRIPT],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        timeout=900)
    out = proc.stdout or ""
    if proc.returncode != 0:
        return None, 0, out
    lines = out.strip().splitlines()
    if lines and lines[-1].strip() == "no changes":
        return None, 0, out
    sha = None
    n = 0
    for line in lines:
        m = re.match(r"committed\s+([0-9a-f]{4,40})\b", line.strip())
        if m:
            sha = m.group(1)
        m = re.match(r"changed/new:\s*(\d+),\s*deleted:\s*(\d+)", line.strip())
        if m:
            n = int(m.group(1)) + int(m.group(2))
    return sha, n, out


def main():
    sha, n, out = run_sync()
    if sha is None and "no changes" not in out:
        # Error path: relay the captured output briefly, fail loudly.
        print(out.strip() or "sync failed with no output")
        return 1
    if sha is None:
        print("no changes.")
        return 0
    print("%s %d files changed" % (sha, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
