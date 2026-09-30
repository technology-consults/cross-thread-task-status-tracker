#!/usr/bin/env python3
"""repo-pull — versioned package entrypoint (run.py).

Behavior-preserving move of the cron body previously executed by the agent:
runs the vendored pull_all_repos.sh, which fast-forwards every clean local
clone under the repo workbench. Repos with uncommitted changes are SKIPPED,
never overwritten; diverged repos are reported, not forced.

The script's stdout (one line per repo: OK / PULLED / SKIP / FAIL) is the
run's result. Non-zero exit on script failure.

Deterministic job: no agent handshake (no exit 10 path).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PULL_SCRIPT = os.path.join(HERE, "pull_all_repos.sh")


def main():
    proc = subprocess.run(
        ["bash", PULL_SCRIPT],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        timeout=1800)
    out = (proc.stdout or "").strip()
    print(out if out else "(no output)")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
