#!/usr/bin/env python3
"""Tests for the holiday-list-update job package.

Unit: window math, canonical-JSON schema, result validation.
Handshake: round-0 emits exit 10 with the calendar task; a valid result
writes the canonical file and runs the vendored sync (stubbed); a
disagreement writes nothing; bad/out-of-window dates write nothing;
5 invalid rounds fail loudly (exit 20). The real sync script is stubbed;
its own validation is tested separately.
Regression: canonical schema matches the existing file's keys.

Run: python -m unittest discover -s tests -t <pkg>
"""
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)

import run as run_mod  # noqa: E402


def load_sync():
    spec = importlib.util.spec_from_file_location(
        "vendored_hsync",
        os.path.join(PKG, "sync_holiday_copies.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestWindow(unittest.TestCase):
    def test_october_run(self):
        s, e = run_mod.window(date(2026, 10, 1))
        self.assertEqual((s.isoformat(), e.isoformat()),
                         ("2026-10-01", "2027-01-31"))

    def test_december_wraps_year(self):
        s, e = run_mod.window(date(2026, 12, 15))
        self.assertEqual((s.isoformat(), e.isoformat()),
                         ("2026-12-01", "2027-03-31"))

    def test_january_run(self):
        s, e = run_mod.window(date(2027, 1, 1))
        self.assertEqual((s.isoformat(), e.isoformat()),
                         ("2027-01-01", "2027-04-30"))


class TestCanonical(unittest.TestCase):
    def test_schema(self):
        doc = run_mod.build_canonical(
            date(2026, 10, 1), date(2026, 10, 1), date(2027, 1, 31),
            ["2026-12-25", "2026-11-26"], "https://nyse", "https://nasdaq")
        self.assertEqual(set(doc), {"updated", "sources", "note", "holidays"})
        self.assertEqual(doc["updated"], "2026-10-01")
        self.assertEqual(doc["sources"], ["https://nyse", "https://nasdaq"])
        self.assertEqual(doc["holidays"], ["2026-11-26", "2026-12-25"])
        self.assertIn("Oct 2026", doc["note"])


class TestSyncValidation(unittest.TestCase):
    def setUp(self):
        self.sync = load_sync()

    def _doc(self, **kw):
        d = {"updated": "2026-10-01", "sources": ["a"],
             "note": "n", "holidays": ["2026-11-26", "2026-12-25"]}
        d.update(kw)
        return d

    def _write(self, doc):
        p = os.path.join(tempfile.mkdtemp(), "h.json")
        with open(p, "w") as f:
            json.dump(doc, f)
        return p

    def test_valid(self):
        text, data = self.sync.load_and_validate(self._write(self._doc()))
        self.assertEqual(len(data["holidays"]), 2)

    def test_rejects_unsorted(self):
        with self.assertRaises(ValueError):
            self.sync.load_and_validate(
                self._write(self._doc(holidays=["2026-12-25", "2026-11-26"])))

    def test_rejects_bad_date(self):
        with self.assertRaises(ValueError):
            self.sync.load_and_validate(
                self._write(self._doc(holidays=["2026-13-99"])))


class TestHandshake(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="holiday-test-")
        os.environ["CRON_JOB_STATE_DIR"] = self.tmp
        self.json_path = os.path.join(self.tmp, "nyse_holidays.json")
        os.environ["CRON_HOLIDAYS_JSON"] = self.json_path

    def tearDown(self):
        del os.environ["CRON_JOB_STATE_DIR"]
        del os.environ["CRON_HOLIDAYS_JSON"]

    def _run(self, argv, sync_rc=0):
        real = run_mod.run_sync_script
        run_mod.run_sync_script = lambda p: (sync_rc, "synced ok")
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = run_mod.main(argv)
        finally:
            run_mod.run_sync_script = real
        return rc, buf.getvalue()

    def _req(self, out):
        block = out.split(run_mod.REQ_BEGIN, 1)[1]
        return json.loads(block.split(run_mod.REQ_END, 1)[0].strip())

    def test_round0_emits_calendar_task(self):
        rc, out = self._run([])
        self.assertEqual(rc, 10)
        req = self._req(out)
        self.assertEqual(req["attempt"], 1)
        self.assertIn("FULL-DAY", req["task"])

    def test_valid_result_writes_and_syncs(self):
        rc, out = self._run([])
        res = {"holidays": ["2026-11-26", "2026-12-25"],
               "nyse_url": "https://nyse", "nasdaq_url": "https://nasdaq",
               "disagreement": None}
        rc2, out2 = self._run(["--agent-result", json.dumps(res)])
        self.assertEqual(rc2, 0)
        self.assertIn("silent: holiday list refreshed", out2)
        with open(self.json_path) as f:
            doc = json.load(f)
        self.assertEqual(doc["holidays"], ["2026-11-26", "2026-12-25"])

    def test_disagreement_writes_nothing(self):
        self._run([])
        res = {"holidays": [],
               "nyse_url": "https://nyse", "nasdaq_url": "https://nasdaq",
               "disagreement": {"date": "2026-12-25",
                                "nyse_says": "closed",
                                "nasdaq_says": "open"}}
        rc2, out2 = self._run(["--agent-result", json.dumps(res)])
        self.assertEqual(rc2, 0)
        self.assertIn("DISAGREE", out2)
        self.assertFalse(os.path.exists(self.json_path))

    def test_bad_dates_write_nothing(self):
        self._run([])
        res = {"holidays": ["not-a-date"],
               "nyse_url": "https://nyse", "nasdaq_url": "https://nasdaq",
               "disagreement": None}
        rc2, out2 = self._run(["--agent-result", json.dumps(res)])
        self.assertEqual(rc2, 0)
        self.assertIn("unusable dates", out2)
        self.assertFalse(os.path.exists(self.json_path))

    def test_sync_failure_reports(self):
        self._run([])
        res = {"holidays": ["2026-11-26"],
               "nyse_url": "https://nyse", "nasdaq_url": "https://nasdaq",
               "disagreement": None}
        rc2, out2 = self._run(["--agent-result", json.dumps(res)],
                              sync_rc=1)
        self.assertEqual(rc2, 0)
        self.assertIn("mirror sync FAILED", out2)
        # local file still written (mirror is the only failure)
        self.assertTrue(os.path.exists(self.json_path))

    def test_invalid_rounds_fail_loudly(self):
        self._run([])
        rc = 10
        for _ in range(4):
            rc, _ = self._run(["--agent-result", json.dumps({"x": 1})])
            self.assertEqual(rc, 10)
        rc, out = self._run(["--agent-result", json.dumps({"x": 1})])
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
