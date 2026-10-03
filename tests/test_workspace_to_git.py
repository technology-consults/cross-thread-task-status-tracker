#!/usr/bin/env python3
"""Unit tests for scripts/workspace_to_git.py (network-free)."""
import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import workspace_to_git as m  # noqa: E402

passed, failed = 0, 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL:", name)


# --- is_work_product ---------------------------------------------------------
_td = tempfile.mkdtemp()
_py = os.path.join(_td, "s.py")
open(_py, "w").write("x")
check("py is work product", m.is_work_product(_py))

_md = os.path.join(_td, "d.md")
open(_md, "w").write("x")
check("md is work product", m.is_work_product(_md))

_mp4 = os.path.join(_td, "v.mp4")
open(_mp4, "w").write("x")
check("mp4 is NOT work product", not m.is_work_product(_mp4))

_pyc = os.path.join(_td, "c.pyc")
open(_pyc, "w").write("x")
check("pyc is NOT work product", not m.is_work_product(_pyc))

# --- find_work_files ---------------------------------------------------------
os.makedirs(os.path.join(_td, "sub", "__pycache__"))
open(os.path.join(_td, "sub", "code.py"), "w").write("x")
open(os.path.join(_td, "sub", "__pycache__", "c.pyc"), "w").write("x")
open(os.path.join(_td, "sub", "vid.mp4"), "w").write("x")
os.makedirs(os.path.join(_td, "hidden_files"))
open(os.path.join(_td, "hidden_files", "state.json"), "w").write("x")

found = m.find_work_files(_td)
names = [os.path.basename(f) for f in found]
check("finds code.py", "code.py" in names)
check("finds s.py", "s.py" in names)
check("excludes pycache", "c.pyc" not in names)
check("excludes mp4", "vid.mp4" not in names)
check("excludes hidden_files", "state.json" not in names)

# --- blob_sha ----------------------------------------------------------------
import hashlib
check("blob_sha matches git",
      m.blob_sha(b"hi") == hashlib.sha1(b"blob 2\0hi").hexdigest())

# --- parse_repo_spec ---------------------------------------------------------
check("parse plain repo",
      m.parse_repo_spec("agent-tools") == ("agent-tools", None))
check("parse repo:subdir",
      m.parse_repo_spec("tracker:crons") == ("tracker", "crons"))

print("%d passed, %d failed" % (passed, failed))
sys.exit(0 if failed == 0 else 1)
