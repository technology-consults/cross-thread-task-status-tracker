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
             ("tree_is_clean", "run_git", "remote_head", "local_tree_sha",
              "download_tarball", "sync_worktree_from_tarball")}
    for k, v in fake.items():
        setattr(m, k, v)
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            rc = m.main(["api_repo_sync.py", "/fake/repo", "fake"])
    finally:
        for k, v in saved.items():
            setattr(m, k, v)
    return rc, buf.getvalue().strip()


FAKE_CLEAN = {
    "tree_is_clean": lambda d: True,
    "run_git": lambda d, *a: (0, "https://github.com/o/r.git", ""),
    "remote_head": lambda o, r: ("abc1234" * 5 + "ab", "tree1"),
    "local_tree_sha": lambda d: "tree1",
    "download_tarball": lambda *a: (_ for _ in ()).throw(
        AssertionError("should not download when in sync")),
    "sync_worktree_from_tarball": lambda *a: (_ for _ in ()).throw(
        AssertionError("should not sync when in sync")),
}
rc, out = run_main_with(FAKE_CLEAN)
check("in-sync -> rc 0", rc == 0)
check("in-sync -> OK line", out.startswith("OK fake: already current"))
check("in-sync -> mentions API verification", "verified via API" in out)


def fake_git_behind(repo_dir, *args):
    if args[:2] == ("config", "--get"):
        return 0, "https://github.com/o/r.git", ""
    if args == ("add", "-A"):
        return 0, "", ""
    if args == ("write-tree",):
        return 0, "tree2", ""
    if args[0] == "commit":
        return 0, "", ""
    if args[:2] == ("reset", "-q"):
        return 0, "", ""
    return 0, "", ""


FAKE_BEHIND = {
    "tree_is_clean": lambda d: True,
    "run_git": fake_git_behind,
    "remote_head": lambda o, r: ("def5678" * 5 + "cd", "tree2"),
    "local_tree_sha": lambda d: "tree1",
    "download_tarball": lambda *a: None,
    "sync_worktree_from_tarball": lambda *a: None,
}
rc, out = run_main_with(FAKE_BEHIND)
check("behind -> rc 0", rc == 0)
check("behind -> PULLED line", out.startswith("PULLED fake:"))
check("behind -> mentions tarball", "API tarball" in out)


FAKE_DIRTY = dict(FAKE_CLEAN)
FAKE_DIRTY["tree_is_clean"] = lambda d: False
rc, out = run_main_with(FAKE_DIRTY)
check("dirty tree -> rc 1", rc == 1)
check("dirty tree -> FAIL line", out.startswith("FAIL fake:"))
check("dirty tree -> refusal reason", "refusing" in out)


def fake_git_bad_tree(repo_dir, *args):
    if args[:2] == ("config", "--get"):
        return 0, "https://github.com/o/r.git", ""
    if args == ("add", "-A"):
        return 0, "", ""
    if args == ("write-tree",):
        return 0, "WRONGTREE", ""
    return 0, "", ""


FAKE_BAD_TREE = {
    "tree_is_clean": lambda d: True,
    "run_git": fake_git_bad_tree,
    "remote_head": lambda o, r: ("def5678" * 5 + "cd", "tree2"),
    "local_tree_sha": lambda d: "tree1",
    "download_tarball": lambda *a: None,
    "sync_worktree_from_tarball": lambda *a: None,
}
rc, out = run_main_with(FAKE_BAD_TREE)
check("tree mismatch -> rc 1", rc == 1)
check("tree mismatch -> FAIL line", out.startswith("FAIL fake:"))
check("tree mismatch -> no commit attempted",
      "aborted" in out)


FAKE_BAD_REMOTE = dict(FAKE_CLEAN)
FAKE_BAD_REMOTE["run_git"] = lambda d, *a: (0, "not a url", "")
rc, out = run_main_with(FAKE_BAD_REMOTE)
check("unparseable remote -> rc 1", rc == 1)
check("unparseable remote -> FAIL line", out.startswith("FAIL fake:"))


print("%d passed, %d failed" % (passed, failed))
sys.exit(0 if failed == 0 else 1)
