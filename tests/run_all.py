#!/usr/bin/env python3
"""
Master regression runner — runs ALL suites.
- tests/regression.py: board (tasks, push safety, CSS, HTML, digests)
- tests/test_portals.py: portals & websites live
- tests/test_crons.py: cron definitions & scripts valid

Run: python3 tests/run_all.py
Exit 0 = everything passes. Non-zero = failures, DO NOT DEPLOY.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES = ["regression.py", "test_portals.py", "test_crons.py"]

total_fail = 0
for suite in SUITES:
    print(f"\n{'='*60}\nRunning {suite}\n{'='*60}")
    r = subprocess.run([sys.executable, os.path.join(HERE, suite)],
                       capture_output=False, timeout=300)
    if r.returncode != 0:
        total_fail += 1
        print(f"SUITE FAILED: {suite}")

print(f"\n{'='*60}")
if total_fail:
    print(f"RESULT: {total_fail} suite(s) failed — DO NOT DEPLOY")
else:
    print("RESULT: all suites passed")
sys.exit(1 if total_fail else 0)
