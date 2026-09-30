#!/usr/bin/env python3
"""Tests for scripts/enforce/no_raw_githubusercontent.py.

Run: python3 tests/test_enforce_no_raw.py
Exit 0 = all pass, non-zero = failures.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "..", "scripts", "enforce",
                     "no_raw_githubusercontent.py")

passed, failed = [], []


def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print("%s: %s" % ("PASS" if cond else "FAIL", name)
          + (" - %s" % detail if detail and not cond else ""))


def run_on(files):
    """Write {relpath: content} to a temp dir, run the check, return rc+out."""
    tmp = tempfile.mkdtemp(prefix="enforce-test-")
    for rel, content in files.items():
        full = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(full, mode) as f:
            f.write(content)
    r = subprocess.run([sys.executable, CHECK, tmp],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       text=True)
    return r.returncode, r.stdout


# --- unit: clean tree passes ---
rc, out = run_on({"a.py": "print('hello')\n",
                  "docs/b.md": "# no urls here\n"})
check("clean tree passes", rc == 0, out)

# --- unit: raw URL fails with file:line and api suggestion ---
rc, out = run_on({"x.py": "URL = 'https://raw.githubusercontent.com/o/r/main/f.py'\n"})
check("raw URL fails", rc != 0, out)
check("names file and line", "x.py:1" in out, out)
check("suggests contents API",
      "api.github.com/repos/o/r/contents/f.py?ref=main" in out, out)

# --- unit: http variant also caught ---
rc, out = run_on({"x.py": "http://raw.githubusercontent.com/o/r/main/f.py\n"})
check("http variant caught", rc != 0, out)

# --- unit: api.github.com URLs do not trip the check ---
rc, out = run_on({"x.py": "URL='https://api.github.com/repos/o/r/contents/f.py?ref=main'\n"})
check("api.github.com URL passes", rc == 0, out)

# --- unit: binary-ish extension skipped ---
rc, out = run_on({"img.png": b"https://raw.githubusercontent.com/o/r/main/x\n"})
check("binary extension skipped", rc == 0, out)

# --- regression: the checker's own repo stays clean ---
r = subprocess.run([sys.executable, CHECK],
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
check("repo tree currently clean", r.returncode == 0, r.stdout[:500])

print("\n%d passed, %d failed" % (len(passed), len(failed)))
sys.exit(1 if failed else 0)
