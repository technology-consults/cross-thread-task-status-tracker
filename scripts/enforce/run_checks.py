#!/usr/bin/env python3
"""Run all mechanically-checkable repo enforcement checks.

Usage: python3 scripts/enforce/run_checks.py [path ...]
Exit 0 = all checks pass. Non-zero = a check failed; do not commit.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = ["no_raw_githubusercontent.py"]

fail = 0
for check in CHECKS:
    path = os.path.join(HERE, check)
    r = subprocess.run([sys.executable, path] + sys.argv[1:])
    if r.returncode != 0:
        fail += 1
        print("CHECK FAILED: %s" % check, file=sys.stderr)

if fail:
    print("RESULT: %d check(s) failed - DO NOT COMMIT" % fail,
          file=sys.stderr)
sys.exit(1 if fail else 0)
