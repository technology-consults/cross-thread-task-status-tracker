#!/usr/bin/env python3
"""Tests for the board-unblock-watch-vh run.py entrypoint.

Unit: empty lists -> silent exit 0 with no agent call; non-empty ->
exit 10 with the per-thread task; valid agent result -> handled ids
recorded + digest; 5 invalid rounds -> exit 20. The vendored watcher is
stubbed (no subprocess, no network).

Run: python -m unittest discover -s tests -t <pkg>
"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)

import run as run_mod  # noqa: E402

UNBLOCKS = [{"id": "t-new", "thread": "vh", "title": "newly unblocked",
             "status": "todo", "due": None, "detail": "do the thing",
             "where": None, "assigned_to": "Bandhu"}]
SWEEP = [{"id": "t-stalled", "thread": "vh", "title": "stalled",
          "status": "in_progress", "due": None, "detail": "",
          "where": None, "assigned_to": "BalRam",
          "reason": "stalled", "owner_hint": "his"}]


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="unblock-run-test-")
        os.environ["CRON_JOB_STATE_DIR"] = self.tmp
        self._orig = run_mod.run_watch
        self.marked = []

        def fake(extra_args):
            if extra_args == []:
                return UNBLOCKS
            if extra_args == ["--sweep"]:
                return SWEEP
            if extra_args[0] == "--mark-handled":
                self.marked = json.loads(extra_args[1])
                return {"handled": self.marked}
            raise AssertionError(extra_args)

        run_mod.run_watch = fake

    def tearDown(self):
        run_mod.run_watch = self._orig
        del os.environ["CRON_JOB_STATE_DIR"]

    def _run(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = run_mod.main(argv)
        return rc, buf.getvalue()

    def _req(self, out):
        block = out.split(run_mod.REQ_BEGIN, 1)[1]
        return json.loads(block.split(run_mod.REQ_END, 1)[0].strip())

    def test_empty_lists_stay_silent(self):
        run_mod.run_watch = lambda extra: []
        rc, out = self._run([])
        self.assertEqual(rc, 0)
        self.assertIn("nothing actionable", out)
        self.assertNotIn(run_mod.REQ_BEGIN, out)

    def test_nonempty_emits_agent_request(self):
        rc, out = self._run([])
        self.assertEqual(rc, 10)
        req = self._req(out)
        self.assertEqual(req["attempt"], 1)
        self.assertIn("t-new", req["task"])
        self.assertIn(run_mod.TRACKER_CHAT, req["task"])

    def test_valid_result_marks_handled(self):
        self._run([])
        rc, out = self._run(["--agent-result", json.dumps(
            {"handled": ["t-new", "t-stalled"],
             "acted": [{"id": "t-new", "action": "did the work",
                        "note": "completed"}],
             "errors": []})])
        self.assertEqual(rc, 0)
        self.assertEqual(sorted(self.marked), ["t-new", "t-stalled"])
        self.assertIn("1 acted, 2 handled, 0 error(s)", out)

    def test_invalid_rounds_fail_loudly(self):
        self._run([])
        rc = 10
        for _ in range(4):
            rc, _ = self._run(["--agent-result", json.dumps(
                {"handled": "not-a-list", "acted": [], "errors": []})])
            self.assertEqual(rc, 10)
        rc, out = self._run(["--agent-result", json.dumps(
            {"handled": "not-a-list", "acted": [], "errors": []})])
        self.assertEqual(rc, 20)
        self.assertIn("failing loudly", out)


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
