#!/usr/bin/env python3
"""Tests for the vendored unblock_watch.py (adapted for the package).

Unit: unblock detection (newly actionable / still blocked / never-gated /
thread filter / handled exclusion), external gate dates, legacy bare-string
blockedBy, sweep reasons (idle / stalled / completed_stalled), recurring
exclusion, mark_handled persistence. GitHub fetch is stubbed in-process.

Run: python -m unittest discover -s tests -t <pkg>
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)


def load_watch():
    spec = importlib.util.spec_from_file_location(
        "vendored_unblock_watch",
        os.path.join(PKG, "unblock_watch.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


THREAD = "sv"


class WatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="unblock-test-")
        os.environ["CRON_JOB_STATE_DIR"] = self.tmp
        self.w = load_watch()

    def tearDown(self):
        del os.environ["CRON_JOB_STATE_DIR"]

    def _tasks(self, today):
        return [
            {"id": "t-done", "thread": THREAD, "status": "done",
             "title": "dep done"},
            {"id": "t-new", "thread": THREAD, "status": "todo",
             "title": "newly unblocked", "blockedBy": ["t-done"]},
            {"id": "t-still", "thread": THREAD, "status": "blocked",
             "title": "still blocked",
             "blockedBy": [{"kind": "task", "id": "t-missing"}]},
            {"id": "t-never", "thread": THREAD, "status": "todo",
             "title": "never gated"},
            {"id": "t-other", "thread": "xx", "status": "todo",
             "title": "other thread", "blockedBy": ["t-done"]},
            {"id": "t-ext-open", "thread": THREAD, "status": "todo",
             "title": "external gate open",
             "blockedBy": [{"kind": "external", "note": "gate 2026-01-01"}]},
            {"id": "t-ext-shut", "thread": THREAD, "status": "todo",
             "title": "external gate shut",
             "blockedBy": [{"kind": "external", "note": "gate 2099-01-01"}]},
            {"id": "t-future-start", "thread": THREAD, "status": "todo",
             "title": "future start", "start": "2099-01-01"},
            {"id": "t-idle", "thread": THREAD, "status": "todo",
             "title": "idle todo", "start": "2026-01-01"},
            {"id": "t-stalled", "thread": THREAD, "status": "in_progress",
             "title": "stalled work", "updated": "2026-01-01"},
            {"id": "t-fresh", "thread": THREAD, "status": "in_progress",
             "title": "fresh work", "updated": today},
            {"id": "t-recur", "thread": THREAD, "status": "in_progress",
             "title": "daily digest cron", "updated": "2026-01-01"},
            {"id": "t-comp", "thread": THREAD, "status": "completed",
             "title": "old completed", "updated": "2026-01-01"},
        ]

    def test_unblocks(self):
        today = "2026-09-30"
        out = self.w.compute_unblocks(self._tasks(today), set(), THREAD,
                                      today)
        ids = sorted(t["id"] for t in out)
        # t-idle (todo with a passed start gate) is a genuine new unblock;
        # it would also appear in the sweep as idle.
        self.assertEqual(ids, ["t-ext-open", "t-idle", "t-new"])

    def test_still_blocked_excluded(self):
        today = "2026-09-30"
        out = self.w.compute_unblocks(self._tasks(today), set(), THREAD,
                                      today)
        ids = [t["id"] for t in out]
        for x in ("t-still", "t-never", "t-other", "t-ext-shut",
                  "t-future-start"):
            self.assertNotIn(x, ids)

    def test_handled_excluded(self):
        today = "2026-09-30"
        out = self.w.compute_unblocks(self._tasks(today), {"t-new"},
                                      THREAD, today)
        self.assertEqual(sorted(t["id"] for t in out),
                         ["t-ext-open", "t-idle"])

    def test_sweep(self):
        today = "2026-09-30"
        out = self.w.compute_sweep(self._tasks(today), set(), THREAD,
                                   today, "2026-09-27")
        by_id = {t["id"]: t["reason"] for t in out}
        self.assertEqual(by_id.get("t-idle"), "idle")
        self.assertEqual(by_id.get("t-stalled"), "stalled")
        self.assertEqual(by_id.get("t-comp"), "completed_stalled")
        self.assertNotIn("t-fresh", by_id)
        self.assertNotIn("t-recur", by_id)
        self.assertNotIn("t-never", by_id)  # never gated: not idle

    def test_mark_handled(self):
        real = self.w.legacy_state_path
        self.w.legacy_state_path = lambda: os.path.join(
            self.tmp, "no-such-legacy.json")
        try:
            self.w.mark_handled(["a", "b"])
            self.w.mark_handled(["b", "c"])
            state = self.w.load_state()
        finally:
            self.w.legacy_state_path = real
        self.assertEqual(sorted(state["handled"]), ["a", "b", "c"])

    def test_seed_from_legacy(self):
        legacy = os.path.join(self.tmp, "legacy")
        os.makedirs(legacy)
        real = self.w.legacy_state_path
        lp = os.path.join(legacy, "unblock_watch_state.json")
        with open(lp, "w") as f:
            json.dump({"handled": ["old-1"]}, f)
        self.w.legacy_state_path = lambda: lp
        try:
            state = self.w.load_state()
        finally:
            self.w.legacy_state_path = real
        self.assertEqual(state["handled"], ["old-1"])

    def test_owner_hint(self):
        self.assertEqual(
            self.w.owner_hint({"assigned_to": "BalRam"}), "his")
        self.assertEqual(
            self.w.owner_hint({"assigned_to": "Bandhu"}), "mine")
        self.assertEqual(
            self.w.owner_hint({"title": "do x (yours)"}), "his")
        self.assertEqual(
            self.w.owner_hint({"title": "do x"}), "mine")


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
