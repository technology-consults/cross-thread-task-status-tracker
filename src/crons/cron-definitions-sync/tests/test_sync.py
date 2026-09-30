#!/usr/bin/env python3
"""Tests for the cron-definitions-sync job package.

Unit: blob_sha, collect() with env-overridden dirs, run.py reply parsing.
Regression: vendored collect() mirrors the original layout (shared/ +
goals/<slug>/, _invalid skipped, index.html rebuilt).

Run: python -m unittest discover -s tests -t <pkg>
"""
import importlib.util
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)

import run as run_mod  # noqa: E402


def load_sync():
    spec = importlib.util.spec_from_file_location(
        "vendored_sync", os.path.join(PKG, "sync_crons_to_git.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class FakeProc:
    def __init__(self, rc, out):
        self.returncode = rc
        self.stdout = out


class TestParseSyncOutput(unittest.TestCase):
    def _parse(self, rc, out):
        # replicate run.py's parsing by monkeypatching subprocess.run
        import subprocess
        real = subprocess.run
        subprocess.run = lambda *a, **k: FakeProc(rc, out)
        try:
            return run_mod.run_sync()
        finally:
            subprocess.run = real

    def test_no_changes(self):
        sha, n, out = self._parse(0, "changed/new: 0, deleted: 0\nno changes\n")
        self.assertIsNone(sha)

    def test_committed(self):
        out = ("changed/new: 3, deleted: 1\n  blob crons/x.md\n"
               "committed abc12345: Crons: sync 51 definitions (2026-09-30)\n")
        sha, n, _ = self._parse(0, out)
        self.assertEqual(sha, "abc12345")
        self.assertEqual(n, 4)

    def test_error(self):
        sha, n, out = self._parse(1, "GitHub API GET ... -> HTTP 500\n")
        self.assertIsNone(sha)
        self.assertIn("HTTP 500", out)


class TestCollect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sync-test-")
        self.cron_d = os.path.join(self.tmp, "cron.d", "daily")
        os.makedirs(self.cron_d)
        with open(os.path.join(self.cron_d, "a__daily.md"), "w") as f:
            f.write("---\nid: a\n---\nbody a\n")
        goals = os.path.join(self.tmp, "goals", "g1", "crons", "hourly")
        os.makedirs(goals)
        with open(os.path.join(goals, "b__interval.md"), "w") as f:
            f.write("---\nid: b\n---\nbody b\n")
        # _invalid dirs must be skipped
        bad = os.path.join(self.tmp, "cron.d", "_invalid")
        os.makedirs(bad)
        with open(os.path.join(bad, "z.md"), "w") as f:
            f.write("bad\n")
        os.environ["CRON_DEFS_DIR"] = os.path.join(self.tmp, "cron.d")
        os.environ["CRON_GOALS_DIR"] = os.path.join(self.tmp, "goals")
        self.sync = load_sync()

    def tearDown(self):
        del os.environ["CRON_DEFS_DIR"]
        del os.environ["CRON_GOALS_DIR"]

    def test_collect_layout(self):
        files = self.sync.collect()
        self.assertIn("crons/shared/daily/a__daily.md", files)
        self.assertIn("crons/goals/g1/hourly/b__interval.md", files)
        self.assertIn("crons/README.md", files)
        self.assertIn("crons/index.html", files)
        self.assertNotIn("crons/shared/_invalid/z.md", files)

    def test_blob_sha_matches_git(self):
        import hashlib
        data = b"hello"
        h = hashlib.sha1()
        h.update(b"blob %d\0" % len(data))
        h.update(data)
        self.assertEqual(self.sync.blob_sha(data), h.hexdigest())

    def test_env_override_used(self):
        self.assertEqual(self.sync.CRON_D, os.environ["CRON_DEFS_DIR"])
        self.assertEqual(self.sync.GOALS, os.environ["CRON_GOALS_DIR"])

    def test_no_workspace_literals(self):
        # CRON-001: no workspace-path literals anywhere in the package.
        # Patterns are built from parts so this test file itself stays clean.
        # __pycache__ is skipped: .pyc files embed source paths but are never
        # committed (the real check scans the git tree).
        import re
        slash, home_dir = "/", "home"
        tilde = chr(126)
        home = slash + home_dir + slash + "hatch" + slash
        pats = [re.compile(tilde + slash + "workspace"),
                re.compile(home + "workspace"),
                re.compile(home),
                re.compile("file:" + slash * 3 + home_dir),
                re.compile("file:" + slash * 2 + tilde + slash)]
        bad = []
        for dirpath, dirnames, fns in os.walk(PKG):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in fns:
                p = os.path.join(dirpath, fn)
                with open(p, encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if any(pat.search(line) for pat in pats):
                            bad.append("%s:%d" % (p, i))
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
