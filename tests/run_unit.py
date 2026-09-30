#!/usr/bin/env python3
"""Unit-tier test runner for the cross-thread-task-status-tracker repo.

Runs the fast, network-free unit tests -- the enforcement-gate suites,
the gates inventory, the remediation protocol, the ruleset version pin,
and the commit orchestrator helpers:

    tests/test_enforce_*.py, tests/test_gates_inventory.py,
    tests/test_remediation.py, tests/test_ruleset_version.py,
    tests/test_commit.py

Usage: python3 tests/run_unit.py
Exit 0 = everything passes. Non-zero = failures, DO NOT COMMIT
(scripts/commit.py runs this first and aborts the commit on failure).

Heavier suites stay OUT of the pre-commit path on purpose:
  - tests/regression.py  (board regression; run before board deploys)
  - tests/test_crons.py  (validates scheduler state on this machine)
  - tests/test_portals.py (hits live websites)

Each test file follows the repo convention: a main() printing
"<N> passed, <M> failed", exit 0 on success, 1 on failure. The runner
trusts the exit code first and parses the counts line as a courtesy.
"""
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTS_RE = re.compile(r"(\d+)\s+passed,\s+(\d+)\s+failed")

FILES = sorted(
    [os.path.basename(p) for p in glob.glob(os.path.join(HERE, "test_*.py"))
     if os.path.basename(p) != "test_portals.py"
     and not os.path.basename(p).startswith("test_cron")]
)


def run_one(path):
    name = os.path.basename(path)
    try:
        r = subprocess.run([sys.executable, path], capture_output=True,
                           text=True, timeout=300, cwd=HERE)
    except subprocess.TimeoutExpired:
        return name, False, 0, 0, "TIMEOUT after 300s"
    except Exception as e:  # noqa: BLE001 - report, don't crash the suite
        return name, False, 0, 0, "RUNNER ERROR: %s" % e
    passed, failed = 0, 0
    for line in r.stdout.splitlines():
        m = COUNTS_RE.search(line)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
    ok = r.returncode == 0 and failed == 0
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    return name, ok, passed, failed, tail


def main():
    total_passed, total_failed, failed_files = 0, 0, []
    for name in FILES:
        fname, ok, passed, failed, tail = run_one(
            os.path.join(HERE, name))
        total_passed += passed
        total_failed += failed
        status = "PASS" if ok else "FAIL"
        print("%s: %s (%d passed, %d failed)" % (status, fname,
                                                passed, failed))
        if not ok:
            failed_files.append(fname)
            print("      last line: %s" % tail[:200])
    print("-" * 60)
    print("unit tier: %d files, %d passed, %d failed"
          % (len(FILES), total_passed, total_failed))
    if failed_files:
        print("FAILED FILES: %s" % ", ".join(failed_files))
        print("DO NOT COMMIT")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
