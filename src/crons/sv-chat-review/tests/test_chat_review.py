#!/usr/bin/env python3
"""Tests for the sv-chat-review job package.

Unit: watermark seeding (goal file present/absent), extraction validation,
filing validation. Handshake: round-0 extract request; empty extraction ->
watermark update + nothing-new line; items -> filing request; filing result
-> digest; 5 invalid rounds -> exit 20. State goes to a temp dir.

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

ITEMS = [
    {"type": "decision", "summary": "use option A",
     "detail": "agreed in thread"},
    {"type": "task", "summary": "build the widget",
     "detail": "builds something"},
]


class ChatReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="chat-review-test-")
        os.environ["CRON_JOB_STATE_DIR"] = self.tmp

    def tearDown(self):
        del os.environ["CRON_JOB_STATE_DIR"]

    def _run(self, argv):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = run_mod.main(argv)
        return rc, buf.getvalue()

    def _req(self, out):
        block = out.split(run_mod.REQ_BEGIN, 1)[1]
        return json.loads(block.split(run_mod.REQ_END, 1)[0].strip())

    def test_seed_from_goal_file(self):
        goal = os.path.join(self.tmp, "workspace", "goals",
                            run_mod.GOAL_HIDDEN, "hidden_files")
        os.makedirs(goal)
        with open(os.path.join(goal, run_mod.SEED_FILE), "w") as f:
            json.dump({"chats": {run_mod.SV_TRACKER_ID:
                                 {"watermark": "msg-42"}}}, f)
        real = run_mod.goal_hidden_dir
        run_mod.goal_hidden_dir = lambda: goal
        try:
            wm = run_mod.load_watermarks()
        finally:
            run_mod.goal_hidden_dir = real
        self.assertEqual(wm["sv"], "msg-42")

    def test_seed_missing_file(self):
        wm = run_mod.load_watermarks()
        self.assertIsNone(wm["sv"])

    def test_round0_extract_request(self):
        rc, out = self._run([])
        self.assertEqual(rc, 10)
        req = self._req(out)
        self.assertEqual(req["attempt"], 1)
        self.assertIn(run_mod.SV_TRACKER_ID, req["task"])
        self.assertIn("proposal", req["task"])

    def test_empty_extraction_updates_watermark(self):
        self._run([])
        rc, out = self._run(["--agent-result", json.dumps(
            {"items": [], "last_seen_message_id": "msg-100"})])
        self.assertEqual(rc, 0)
        self.assertIn("nothing new", out)
        with open(run_mod.watermarks_path()) as f:
            wm = json.load(f)
        self.assertEqual(wm["sv"], "msg-100")

    def test_extraction_then_filing(self):
        self._run([])
        rc, out = self._run(["--agent-result", json.dumps(
            {"items": ITEMS, "last_seen_message_id": "msg-101"})])
        self.assertEqual(rc, 10)
        req = self._req(out)
        self.assertIn("Filing rules", req["task"])
        self.assertIn("credentials", req["task"])
        rc2, out2 = self._run(["--agent-result", json.dumps(
            {"filed": [
                {"summary": "use option A", "action": "doc update",
                 "detail": "short-video docs/plan.md"},
                {"summary": "build the widget", "action": "board task",
                 "detail": "sv.build-widget [BUILD]"}],
             "errors": []})])
        self.assertEqual(rc2, 0)
        self.assertIn("2 extracted, 2 filed, 0 error(s)", out2)
        self.assertIn("short-video docs/plan.md", out2)
        with open(run_mod.watermarks_path()) as f:
            wm = json.load(f)
        self.assertEqual(wm["sv"], "msg-101")

    def test_filing_errors_listed(self):
        self._run([])
        self._run(["--agent-result", json.dumps(
            {"items": ITEMS, "last_seen_message_id": "msg-101"})])
        rc, out = self._run(["--agent-result", json.dumps(
            {"filed": [], "errors": ["could not reach board API"]})])
        self.assertEqual(rc, 0)
        self.assertIn("ERROR: could not reach board API", out)

    def test_bad_item_type_rejected(self):
        self._run([])
        rc, _ = self._run(["--agent-result", json.dumps(
            {"items": [{"type": "chat", "summary": "x"}],
             "last_seen_message_id": "m"})])
        self.assertEqual(rc, 10)  # asked again

    def test_invalid_rounds_fail_loudly(self):
        self._run([])
        rc = 10
        for _ in range(4):
            rc, _ = self._run(["--agent-result", json.dumps(
                {"bogus": True})])
            self.assertEqual(rc, 10)
        rc, out = self._run(["--agent-result", json.dumps({"bogus": True})])
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
