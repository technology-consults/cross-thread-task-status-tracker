#!/usr/bin/env python3
"""Tests for the failure-log-weekly job package.

Unit: entry parsing (Entries heading scoping, date extraction, malformed
lines, invalid dates), 7-day window filtering, and the three reply paths
(missing file / entries / no entries). GitHub fetch is stubbed.

Run: python -m unittest discover -s tests -t <pkg>
"""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)

import run as run_mod  # noqa: E402

SAMPLE = """# Failure Log

Some intro text with 1. 2026-01-01 \u2014 not an entry.

## Entries (newest last)

1. 2026-09-24 \u2014 first failure
2. 2026-09-27 \u2014 second failure
3. 2026-09-29 \u2014 third failure
4. 2026-09-20 \u2014 older than window
5. not-a-date \u2014 malformed
6. 2026-13-99 \u2014 invalid date

## Notes

1. 2026-09-28 \u2014 not an entry (wrong section)
"""


class TestParse(unittest.TestCase):
    def test_entries_scoped_to_heading(self):
        entries, unparsed = run_mod.parse_entries(SAMPLE)
        dates = sorted(d.isoformat() for d, _ in entries)
        self.assertEqual(dates, ["2026-09-20", "2026-09-24",
                                 "2026-09-27", "2026-09-29"])
        self.assertEqual(len(unparsed), 2)

    def test_descriptions(self):
        entries, _ = run_mod.parse_entries(SAMPLE)
        descs = {d.isoformat(): t for d, t in entries}
        self.assertEqual(descs["2026-09-29"], "third failure")


class TestReplies(unittest.TestCase):
    def setUp(self):
        self._orig_today = run_mod.today

    def tearDown(self):
        run_mod.today = self._orig_today

    def _run(self, text):
        real = run_mod.fetch_failures
        if text is None:
            run_mod.fetch_failures = lambda: None
        else:
            run_mod.fetch_failures = lambda: text
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = run_mod.main()
        finally:
            run_mod.fetch_failures = real
        return rc, buf.getvalue()

    def test_missing_file_graceful(self):
        rc, out = self._run(None)
        self.assertEqual(rc, 0)
        self.assertIn("verifier/failures.md not found", out)
        self.assertIn("no chat delivery", out)

    def test_entries_in_window(self):
        run_mod.today = staticmethod(lambda: date(2026, 9, 30))
        rc, out = self._run(SAMPLE)
        self.assertEqual(rc, 0)
        self.assertIn("3 new failure(s)", out)
        self.assertIn("2026-09-29", out)
        self.assertIn("2026-09-24", out)
        self.assertNotIn("2026-09-20", out)  # older than window
        self.assertNotIn("2026-09-28", out)  # wrong section
        # newest first
        self.assertLess(out.index("2026-09-29"), out.index("2026-09-24"))
        self.assertIn("could not be parsed", out)  # 2 malformed lines

    def test_window_boundary_inclusive(self):
        run_mod.today = staticmethod(lambda: date(2026, 9, 30))
        rc, out = self._run("## Entries\n\n1. 2026-09-24 \u2014 edge\n")
        self.assertIn("1 new failure(s)", out)

    def test_no_entries_in_window(self):
        run_mod.today = staticmethod(lambda: date(2026, 9, 30))
        rc, out = self._run("## Entries\n\n1. 2026-09-10 \u2014 old\n")
        self.assertEqual(rc, 0)
        self.assertIn("no new failures", out)

    def test_future_date_excluded(self):
        run_mod.today = staticmethod(lambda: date(2026, 9, 30))
        rc, out = self._run("## Entries\n\n1. 2026-10-05 \u2014 future\n")
        self.assertIn("no new failures", out)


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
