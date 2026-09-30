#!/usr/bin/env python3
"""Tests for the repo-pull job package.

Unit: run.py relays the vendored script's stdout and exit code.
Functional: run the vendored script against a fake repos dir (env override)
  - a non-git dir -> SKIP (not a git repo)
  - a git repo with no origin -> SKIP/FAIL without touching anything
Regression: script refuses to discard local changes (dirty repo -> SKIP).

Run: python -m unittest discover -s tests -t <pkg>
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)

import run as run_mod  # noqa: E402

SCRIPT = os.path.join(PKG, "pull_all_repos.sh")


def run_script_with_env(repos_dir):
    env = dict(os.environ, CRON_REPOS_DIR=repos_dir)
    r = subprocess.run(["bash", SCRIPT], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, env=env,
                       timeout=120)
    return r.returncode, r.stdout


class TestRunRelay(unittest.TestCase):
    def test_relay(self):
        real = subprocess.run

        class P:
            returncode = 0
            stdout = "OK a: already current (abc123)\n"

        subprocess.run = lambda *a, **k: P()
        try:
            import io
            from contextlib import redirect_stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = run_mod.main()
            self.assertEqual(rc, 0)
            self.assertIn("OK a: already current", buf.getvalue())
        finally:
            subprocess.run = real


class TestScriptFunctional(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="repos-test-")

    def test_non_git_dir_skipped(self):
        os.makedirs(os.path.join(self.tmp, "notarepo"))
        rc, out = run_script_with_env(self.tmp)
        self.assertIn("SKIP notarepo: not a git repo", out)

    def test_git_repo_without_origin(self):
        d = os.path.join(self.tmp, "lonely")
        os.makedirs(d)
        subprocess.run(["git", "init", "-q", d], check=True)
        subprocess.run(["git", "-C", d, "config", "user.email", "t@t"],
                       check=True)
        subprocess.run(["git", "-C", d, "config", "user.name", "t"],
                       check=True)
        subprocess.run(["git", "-C", d, "commit", "-q", "--allow-empty",
                        "-m", "x"], check=True)
        rc, out = run_script_with_env(self.tmp)
        self.assertIn("lonely", out)
        # fetch fails (no origin) -> FAIL line, repo untouched
        self.assertTrue("FAIL lonely: fetch failed" in out
                        or "SKIP lonely" in out)

    def test_dirty_repo_skipped(self):
        d = os.path.join(self.tmp, "dirty")
        os.makedirs(d)
        subprocess.run(["git", "init", "-q", d], check=True)
        with open(os.path.join(d, "f.txt"), "w") as f:
            f.write("uncommitted\n")
        rc, out = run_script_with_env(self.tmp)
        self.assertIn("SKIP dirty: local changes present", out)


class TestNoWorkspaceLiterals(unittest.TestCase):
    def test_clean(self):
        import re
        slash = "/"
        tilde = chr(126)
        home = slash + "home" + slash + "hatch" + slash
        pats = [re.compile(tilde + slash + "workspace"),
                re.compile(home + "workspace"),
                re.compile(home),
                re.compile("file:" + slash * 3 + "home"),
                re.compile("file:" + slash * 2 + tilde + slash)]
        bad = []
        for dirpath, dirnames, fns in os.walk(PKG):
            dirnames[:] = [x for x in dirnames if x != "__pycache__"]
            for fn in fns:
                p = os.path.join(dirpath, fn)
                with open(p, encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f, 1):
                        if any(pat.search(line) for pat in pats):
                            bad.append("%s:%d" % (p, i))
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
