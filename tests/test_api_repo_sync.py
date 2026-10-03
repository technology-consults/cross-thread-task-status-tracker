#!/usr/bin/env python3
"""Unit tests for scripts/api_repo_sync.py (network-free).

Covers: auth-failure detection, owner/repo parsing, the clean-tree gate,
the in-sync shortcut, the tree-SHA-must-match gate, and refusal on dirty
trees. Network and git are faked; no real API or subprocess calls escape.
"""
import io
import os
import sys
import types
from contextlib import redirect_stdout

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
import api_repo_sync as m  # noqa: E402

passed, failed = 0, 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL:", name)


# --- is_auth_failure -------------------------------------------------------
check("auth: could not read Username",
      m.is_auth_failure("fatal: could not read Username for "
                        "'https://github.com': No such device or address"))
check("auth: authentication failed",
      m.is_auth_failure("remote: Invalid username or password. "
                        "fatal: Authentication failed"))
check("auth: permission denied",
      m.is_auth_failure("ERROR: Permission denied (publickey)"))
check("auth: repository not found",
      m.is_auth_failure("remote: Repository not found."))
check("auth: network error is not auth failure",
      not m.is_auth_failure("fatal: unable to connect to github.com"))
check("auth: empty stderr is not auth failure",
      not m.is_auth_failure(""))
check("auth: None is not auth failure",
      not m.is_auth_failure(None))

# --- parse_owner_repo ------------------------------------------------------
check("parse https url",
      m.parse_owner_repo("https://github.com/technology-consults/short-video.git")
      == ("technology-consults", "short-video"))
check("parse https url no .git",
      m.parse_owner_repo("https://github.com/o/r") == ("o", "r"))
check("parse ssh url",
      m.parse_owner_repo("git@github.com:o/r.git") == ("o", "r"))
check("parse garbage -> None",
      m.parse_owner_repo("not a url") is None)
check("parse empty -> None",
      m.parse_owner_repo("") is None)
check("parse None -> None",
      m.parse_owner_repo(None) is None)


# --- main() flow with fakes ------------------------------------------------
class FakeMod(types.SimpleNamespace):
    pass


def run_main_with(fake):
    """Run main() with module-level functions stubbed; capture stdout."""
    saved = {k: getattr(m, k) for k in
             ("run_git", "remote_head", "local_tree_sha",
              "download_tarball", "sync_worktree_from_tarball")}
    for k, v in fake.items():
        setattr(m, k, v)
    real_isdir = os.path.isdir
    os.path.isdir = lambda p: True
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = m.main(["api_repo_sync.py", "/fake/repo", "fake"])
    finally:
        for k, v in saved.items():
            setattr(m, k, v)
        os.path.isdir = real_isdir
    return rc, buf.getvalue().strip()


def make_git(head_tree, index_tree):
    """Fake run_git: config -> url; add -> ok; write-tree -> index_tree;
    reset -> ok; commit -> ok."""
    def fake_git(repo_dir, *args):
        if args[:2] == ("config", "--get"):
            return 0, "https://github.com/o/r.git", ""
        if args == ("add", "-A"):
            return 0, "", ""
        if args == ("write-tree",):
            return 0, index_tree, ""
        if args[:2] == ("reset", "-q"):
            return 0, "", ""
        if args[0] == "commit":
            return 0, "", ""
        return 0, "", ""
    return fake_git


def boom_download(*a):
    raise AssertionError("should not download when in sync")


def boom_sync(*a):
    raise AssertionError("should not sync when in sync")


# In sync, clean tree: HEAD tree == index tree == remote tree -> OK.
FAKE_CLEAN = {
    "run_git": make_git("tree1", "tree1"),
    "remote_head": lambda o, r: ("abc1234" * 5 + "ab", "tree1"),
    "local_tree_sha": lambda d: "tree1",
    "download_tarball": boom_download,
    "sync_worktree_from_tarball": boom_sync,
}
rc, out = run_main_with(FAKE_CLEAN)
check("in-sync -> rc 0", rc == 0)
check("in-sync -> OK line", out.startswith("OK fake: already current"))
check("in-sync -> mentions API verification", "verified via API" in out)

# Phantom flags: worktree == remote tree, HEAD stale -> OK + sync commit.
FAKE_PHANTOM = {
    "run_git": make_git("oldtree", "tree2"),
    "remote_head": lambda o, r: ("def5678" * 5 + "cd", "tree2"),
    "local_tree_sha": lambda d: "oldtree",
    "download_tarball": boom_download,
    "sync_worktree_from_tarball": boom_sync,
}
rc, out = run_main_with(FAKE_PHANTOM)
check("phantom -> rc 0", rc == 0)
check("phantom -> OK line", out.startswith("OK fake: already current"))
check("phantom -> notes flags cleared", "phantom" in out)

# Behind, clean: HEAD == index != remote -> tarball sync -> PULLED.
FAKE_BEHIND = {
    "run_git": make_git("tree1", "tree1"),
    "remote_head": lambda o, r: ("def5678" * 5 + "cd", "tree2"),
    "local_tree_sha": lambda d: "tree1",
    "download_tarball": lambda *a: None,
    "sync_worktree_from_tarball": lambda *a: None,
}
# write-tree after re-add must return the remote tree for the gate to pass.
calls = {"n": 0}
orig_git = FAKE_BEHIND["run_git"]
def behind_git(d, *a):
    if a == ("write-tree",):
        calls["n"] += 1
        return 0, "tree2" if calls["n"] > 1 else "tree1", ""
    return orig_git(d, *a)
FAKE_BEHIND["run_git"] = behind_git
rc, out = run_main_with(FAKE_BEHIND)
check("behind -> rc 0", rc == 0)
check("behind -> PULLED line", out.startswith("PULLED fake:"))
check("behind -> mentions tarball", "API tarball" in out)

# Real local changes: index != remote and HEAD != index -> SKIP.
FAKE_DIRTY = {
    "run_git": make_git("tree1", "dirtytree"),
    "remote_head": lambda o, r: ("def5678" * 5 + "cd", "tree2"),
    "local_tree_sha": lambda d: "tree1",
    "download_tarball": boom_download,
    "sync_worktree_from_tarball": boom_sync,
}
rc, out = run_main_with(FAKE_DIRTY)
check("dirty tree -> rc 0", rc == 0)
check("dirty tree -> SKIP line", out.startswith("SKIP fake:"))
check("dirty tree -> untouched reason", "leaving untouched" in out)

# Tree mismatch after sync staging -> FAIL, no commit.
_wt_calls = {"n": 0}
def bad_tree_git(d, *a):
    if a == ("write-tree",):
        _wt_calls["n"] += 1
        # first call (pre-sync check): clean but behind; second call
        # (post-tarball gate): wrong tree -> abort.
        return 0, "tree1" if _wt_calls["n"] == 1 else "WRONGTREE", ""
    return make_git("tree1", "tree1")(d, *a)
FAKE_BAD_TREE = {
    "run_git": bad_tree_git,
    "remote_head": lambda o, r: ("def5678" * 5 + "cd", "tree2"),
    "local_tree_sha": lambda d: "tree1",
    "download_tarball": lambda *a: None,
    "sync_worktree_from_tarball": lambda *a: None,
}
rc, out = run_main_with(FAKE_BAD_TREE)
check("tree mismatch -> rc 1", rc == 1)
check("tree mismatch -> FAIL line", out.startswith("FAIL fake:"))
check("tree mismatch -> no commit attempted", "aborted" in out)

# Unparseable remote -> SKIP.
FAKE_BAD_REMOTE = dict(FAKE_CLEAN)
FAKE_BAD_REMOTE["run_git"] = lambda d, *a: (0, "not a url", "")
rc, out = run_main_with(FAKE_BAD_REMOTE)
check("unparseable remote -> rc 0", rc == 0)
check("unparseable remote -> SKIP line", out.startswith("SKIP fake:"))


print("%d passed, %d failed" % (passed, failed))
sys.exit(0 if failed == 0 else 1)
