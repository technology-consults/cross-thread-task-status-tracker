#!/usr/bin/env python3
"""Tests for the task-due-date-watch job package.

Unit: bucketing, flagged_by_thread, refresh_asof, result validation.
Handshake: round-0 emits exit 10 with a parseable request block; a valid
--agent-result validates, logs, and exits 0; an invalid one re-asks with
attempt+1; 5 bad rounds fail loudly (exit 20). Network is stubbed; state
goes to a temp dir via CRON_JOB_STATE_DIR.

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


def sample_tasks():
    return [
        {"id": "a", "thread": "sv", "title": "Overdue",
         "status": "todo", "due": "2026-09-28"},
        {"id": "b", "thread": "tr", "title": "Today",
         "status": "blocked", "due": "2026-09-30"},
        {"id": "c", "thread": "vh", "title": "In 2d",
         "status": "todo", "due": "2026-10-02"},
        {"id": "d", "thread": "sv", "title": "In 5d",
         "status": "todo", "due": "2026-10-05"},
        {"id": "e", "thread": "sv", "title": "Far",
         "status": "todo", "due": "2026-12-01"},
        {"id": "f", "thread": "sv", "title": "Agreed",
         "status": "agreed", "due": "2026-09-28"},
        {"id": "g", "thread": "sv", "title": "No due", "status": "todo"},
    ]


class TestBucketing(unittest.TestCase):
    def test_buckets(self):
        self.assertEqual(run_mod.bucket(-3), "OVERDUE")
        self.assertEqual(run_mod.bucket(0), "DUE TODAY")
        self.assertEqual(run_mod.bucket(1), "DUE WITHIN 2 DAYS")
        self.assertEqual(run_mod.bucket(2), "DUE WITHIN 2 DAYS")
        self.assertEqual(run_mod.bucket(7), "DUE THIS WEEK")
        self.assertIsNone(run_mod.bucket(8))

    def test_flagged_by_thread(self):
        flagged = run_mod.flagged_by_thread(sample_tasks(), "2026-09-30")
        self.assertEqual(set(flagged), {"sv", "tr", "vh"})
        self.assertTrue(any("OVERDUE" in ln for ln in flagged["sv"]))
        self.assertTrue(any("DUE TODAY" in ln for ln in flagged["tr"]))
        self.assertTrue(any("DUE WITHIN 2 DAYS" in ln for ln in flagged["vh"]))
        # agreed / no-due / far-future tasks are not flagged
        all_lines = "\n".join(sum(flagged.values(), []))
        self.assertNotIn("| Agreed |", all_lines)
        self.assertNotIn("| No due |", all_lines)
        self.assertNotIn("| Far |", all_lines)

    def test_refresh_asof(self):
        changed, doc = run_mod.refresh_asof({"meta": {"asOf": "2026-09-29",
                                                      "lastUpdated": "x"}},
                                            "2026-09-30")
        self.assertTrue(changed)
        self.assertEqual(doc["meta"]["asOf"], "2026-09-30")
        self.assertEqual(doc["meta"]["lastUpdated"], "x")  # untouched
        changed, _ = run_mod.refresh_asof(doc, "2026-09-30")
        self.assertFalse(changed)


class TestValidation(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(run_mod.validate_result(
            {"posted": ["chat1"], "notes": {}}, run_mod.ALERT_SCHEMA))

    def test_missing_required(self):
        self.assertIn("posted", run_mod.validate_result(
            {"notes": {}}, run_mod.ALERT_SCHEMA))

    def test_wrong_type(self):
        self.assertIsNotNone(run_mod.validate_result(
            {"posted": "chat1"}, run_mod.ALERT_SCHEMA))


class TestHandshake(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="watch-test-")
        os.environ["CRON_JOB_STATE_DIR"] = self.tmp
        os.environ["CRON_MEMORY_DIR"] = os.path.join(self.tmp, "memory")
        self.doc = {"meta": {"asOf": "2026-09-30", "lastUpdated": "x"},
                    "tasks": sample_tasks()}

    def tearDown(self):
        del os.environ["CRON_JOB_STATE_DIR"]
        del os.environ["CRON_MEMORY_DIR"]

    def _run(self, argv):
        real_get = run_mod.get_contents
        real_put = run_mod.put_contents
        run_mod.get_contents = lambda r, p, ref="main": (
            json.dumps(self.doc), "sha123")
        run_mod.put_contents = lambda *a, **k: "commit1"
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = run_mod.main(argv)
        finally:
            run_mod.get_contents = real_get
            run_mod.put_contents = real_put
        return rc, buf.getvalue()

    def _extract_request(self, out):
        block = out.split(run_mod.REQ_BEGIN, 1)[1]
        block = block.split(run_mod.REQ_END, 1)[0]
        return json.loads(block.strip())

    def test_round0_emits_request(self):
        rc, out = self._run([])
        self.assertEqual(rc, 10)
        req = self._extract_request(out)
        self.assertEqual(
            set(req), {"need", "task", "schema", "attempt"})
        self.assertEqual(req["attempt"], 1)
        self.assertIn("d82796e3-56f1-4d34-bf51-665165a38e92",
                      req["task"])  # sv tracker chat id present

    def test_valid_result_completes(self):
        rc, out = self._run([])
        req = self._extract_request(out)
        rc2, out2 = self._run(["--agent-result",
                               json.dumps({"posted": ["c1", "c2"]})])
        self.assertEqual(rc2, 0)
        self.assertIn("2 chat(s)", out2)
        # round state cleaned up
        self.assertFalse(os.path.exists(run_mod.round_state_path()))
        self.assertEqual(req["attempt"], 1)

    def test_invalid_result_reasks_then_fails_loudly(self):
        rc, out = self._run([])
        for attempt in (1, 2, 3, 4):
            rc, out = self._run(["--agent-result",
                                 json.dumps({"nope": True})])
            self.assertEqual(rc, 10, "round %d" % attempt)
            req = self._extract_request(out)
            self.assertEqual(req["attempt"], attempt + 1)
        rc, out = self._run(["--agent-result",
                             json.dumps({"nope": True})])
        self.assertEqual(rc, 20)  # fail loudly after 5 rounds
        self.assertIn("failing loudly", out)

    def test_no_flagged_stays_quiet(self):
        self.doc["tasks"] = [dict(t, due="2027-01-01")
                             for t in sample_tasks()]
        rc, out = self._run([])
        self.assertEqual(rc, 0)
        self.assertIn("zero tasks flagged", out)


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
