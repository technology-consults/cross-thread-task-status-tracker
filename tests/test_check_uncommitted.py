#!/usr/bin/env python3
"""Unit tests for scripts/check_uncommitted.py (network-free where possible).

Covers: blob SHA computation, worktree hashing, phantom vs real
classification with a faked API, and the no-.git / unparseable-remote
SKIP paths.
"""
import hashlib
import os
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import check_uncommitted as m  # noqa: E402

passed, failed = 0, 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL:", name)


# --- blob_sha / worktree_hash ------------------------------------------------
check("blob_sha matches git hash-object",
      m.blob_sha(b"hello\n") ==
      hashlib.sha1(b"blob 6\0hello\n").hexdigest())

_td = tempfile.mkdtemp()
_fp = os.path.join(_td, "f.txt")
with open(_fp, "wb") as fh:
    fh.write(b"data")
check("worktree_hash matches blob_sha",
      m.worktree_hash(_fp) == m.blob_sha(b"data"))

# --- check_repo with faked git + API -----------------------------------------
_real = {k: getattr(m, k) for k in
         ("run_git", "remote_blob_sha", "parse_owner_repo")}


def fake_git_clean(repo_dir, *args):
    if args[:2] == ("config", "--get"):
        return 0, "https://github.com/o/r.git", ""
    if args[:2] == ("status", "--porcelain"):
        return 0, " M changed.py\n?? new.txt\n", ""
    return 0, "", ""


def set_fakes(git_fn, blob_fn):
    m.run_git = git_fn
    m.remote_blob_sha = blob_fn
    m.parse_owner_repo = lambda u: ("o", "r")


# changed.py matches remote -> phantom, ignored; new.txt differs -> flagged.
os.makedirs(os.path.join(_td, ".git"))
with open(os.path.join(_td, "changed.py"), "wb") as fh:
    fh.write(b"same")
with open(os.path.join(_td, "new.txt"), "wb") as fh:
    fh.write(b"local-only")
set_fakes(fake_git_clean,
          lambda o, r, p: m.blob_sha(b"same") if p == "changed.py" else "other")
flagged = m.check_repo(_td, "fake")
check("phantom file ignored, real file flagged",
      len(flagged) == 1 and flagged[0][0] == "new.txt")
check("flagged file carries age", flagged[0][1] >= 0)

# No .git -> reported.
set_fakes(fake_git_clean, lambda o, r, p: None)
flagged = m.check_repo(tempfile.mkdtemp(), "nogit")
check("missing .git reported",
      len(flagged) == 1 and ".git" in flagged[0][0])

# Unparseable remote -> reported.
m.parse_owner_repo = lambda u: None
flagged = m.check_repo(_td, "badremote")
check("unparseable remote reported",
      len(flagged) == 1 and "remote" in flagged[0][0].lower())

for k, v in _real.items():
    setattr(m, k, v)

print("%d passed, %d failed" % (passed, failed))
sys.exit(0 if failed == 0 else 1)
