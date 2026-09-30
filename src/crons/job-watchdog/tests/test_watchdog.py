#!/usr/bin/env python3
"""Tests for the job-watchdog job package.

Unit: window rules (live-bundle active/inactive, NYSE extension, disabled
skip, failed-latest, missed-run), trading-day logic, result validation.
Handshake: round-0 emits exit 10; valid result -> healthy line; problems ->
problem list + daily log; 5 invalid rounds -> exit 20. Network stubbed;
state and memory go to temp dirs.

Run: python -m unittest discover -s tests -t <pkg>
"""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
sys.path.insert(0, PKG)

import run as run_mod  # noqa: E402

TZ = run_mod.TZ


def at(dt):
    return dt.isoformat()


def entry(job_id, enabled=True, runs=()):
    return {"id": job_id, "enabled": enabled,
            "runs": [{"at": a, "status": s, "error": e}
                     for a, s, e in runs]}


def now_at(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=TZ)


class TestRules(unittest.TestCase):
    def _eval(self, now, jobs_data, holidays=()):
        runs_by_id = {e["id"]: e for e in jobs_data}
        return run_mod.evaluate(now, True, set(holidays), runs_by_id)

    def _fill_others_healthy(self, now, jobs, skip=()):
        for job_id, _, _ in run_mod.WATCH:
            if job_id in skip or any(e["id"] == job_id for e in jobs):
                continue
            if job_id == "etf-live-bundle":
                jobs.append(entry(job_id, True,
                                  [(at(now - timedelta(minutes=5)),
                                    "completed", None)]))
            else:
                jobs.append(entry(job_id, True,
                                  [(at(now - timedelta(hours=1)),
                                    "completed", None)]))
        return jobs

    def _all_healthy(self, now, holidays=()):
        jobs = []
        for job_id, base, etf in run_mod.WATCH:
            if job_id == "etf-live-bundle":
                jobs.append(entry(job_id, True, [(at(now - timedelta(
                    minutes=5)), "completed", None)]))
            else:
                jobs.append(entry(job_id, True, [(at(now - timedelta(
                    hours=1)), "completed", None)]))
        return self._eval(now, jobs, holidays)

    def test_all_healthy_weekday(self):
        # Wed 2026-09-30 06:05 ET: trading day, live bundle active.
        now = now_at(2026, 9, 30, 6, 5)
        problems, _ = self._all_healthy(now)
        self.assertEqual(problems, [])

    def test_live_bundle_missed_in_active_hours(self):
        now = now_at(2026, 9, 30, 10, 0)  # Wed, active
        jobs = [entry("etf-live-bundle", True,
                      [(at(now - timedelta(hours=2)), "completed", None)])]
        jobs = self._fill_others_healthy(now, jobs)
        problems, _ = self._eval(now, jobs)
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0][0], "etf-live-bundle")
        self.assertIn("30 min", problems[0][1])

    def test_live_bundle_relaxed_outside_hours(self):
        now = now_at(2026, 9, 30, 23, 30)  # night: 3-day window
        jobs = [entry("etf-live-bundle", True,
                      [(at(now - timedelta(days=2)), "completed", None)])]
        jobs = self._fill_others_healthy(now, jobs)
        problems, _ = self._eval(now, jobs)
        self.assertEqual(problems, [])

    def test_weekend_extends_etf_windows(self):
        now = now_at(2026, 10, 3, 12, 0)  # Saturday
        jobs = []
        for job_id, _, _ in run_mod.WATCH:
            # last completed run Friday morning: >30h ago for dailies
            jobs.append(entry(job_id, True,
                              [(at(now - timedelta(days=1, hours=2)),
                                "completed", None)]))
        problems, _ = self._eval(now, jobs)
        # ETF jobs extended to 3 days -> healthy; non-ETF dailies (30h)
        # with a 26h-old run -> healthy too. Nothing should fire.
        self.assertEqual(problems, [])

    def test_weekend_etf_missed_beyond_3_days(self):
        now = now_at(2026, 10, 4, 12, 0)  # Sunday
        jobs = [entry("etf-price-updates", True,
                      [(at(now - timedelta(days=4)), "completed", None)])]
        jobs = self._fill_others_healthy(now, jobs)
        problems, _ = self._eval(now, jobs)
        self.assertEqual(len(problems), 1)
        self.assertIn("3 days", problems[0][1])

    def test_failed_latest_is_problem(self):
        now = now_at(2026, 9, 30, 9, 0)
        jobs = [entry("repo-pull", True,
                      [(at(now - timedelta(hours=1)), "failed", "boom"),
                       (at(now - timedelta(hours=25)), "completed", None)])]
        jobs = self._fill_others_healthy(now, jobs)
        problems, _ = self._eval(now, jobs)
        self.assertEqual(len(problems), 1)
        self.assertIn("FAILED", problems[0][1])
        self.assertIn("boom", problems[0][1])

    def test_disabled_skipped(self):
        now = now_at(2026, 9, 30, 9, 0)
        jobs = [entry("repo-pull", False, [])]
        jobs = self._fill_others_healthy(now, jobs)
        problems, _ = self._eval(now, jobs)
        self.assertEqual(problems, [])

    def test_missing_job_data_is_problem(self):
        now = now_at(2026, 9, 30, 9, 0)
        problems, _ = self._eval(now, [])
        self.assertEqual(len(problems), len(run_mod.WATCH))

    def test_market_holiday_extends(self):
        now = now_at(2026, 11, 26, 12, 0)  # Thanksgiving (in holiday list)
        jobs = [entry("etf-price-updates", True,
                      [(at(now - timedelta(days=2)), "completed", None)])]
        jobs = self._fill_others_healthy(now, jobs)
        problems, _ = self._eval(now, jobs, holidays={"2026-11-26"})
        self.assertEqual(problems, [])


class TestValidation(unittest.TestCase):
    def test_valid(self):
        self.assertIsNone(run_mod.validate_result(
            {"jobs": [{"id": "a", "enabled": True, "runs": []}]}))

    def test_missing_jobs(self):
        self.assertIsNotNone(run_mod.validate_result({}))

    def test_bad_run_entry(self):
        self.assertIsNotNone(run_mod.validate_result(
            {"jobs": [{"id": "a", "runs": [{"at": "x"}]}]}))


class TestHandshake(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="watchdog-test-")
        os.environ["CRON_JOB_STATE_DIR"] = self.tmp
        os.environ["CRON_MEMORY_DIR"] = os.path.join(self.tmp, "memory")

    def tearDown(self):
        del os.environ["CRON_JOB_STATE_DIR"]
        del os.environ["CRON_MEMORY_DIR"]

    def _run(self, argv, holidays=("2026-11-26",)):
        real_mh = run_mod.market_holidays
        run_mod.market_holidays = lambda: set(holidays)
        buf = io.StringIO()
        try:
            with redirect_stdout(buf):
                rc = run_mod.main(argv)
        finally:
            run_mod.market_holidays = real_mh
        return rc, buf.getvalue()

    def _req(self, out):
        block = out.split(run_mod.REQ_BEGIN, 1)[1]
        return json.loads(block.split(run_mod.REQ_END, 1)[0].strip())

    def _healthy_payload(self, now):
        return {"jobs": [
            entry(j, True, [(at(now - timedelta(minutes=10)), "completed",
                             None)]) for j, _, _ in run_mod.WATCH]}

    def test_round0_emits_request(self):
        rc, out = self._run([])
        self.assertEqual(rc, 10)
        req = self._req(out)
        self.assertEqual(set(req), {"need", "task", "schema", "attempt"})
        for j, _, _ in run_mod.WATCH:
            self.assertIn(j, req["task"])

    def test_healthy_result(self):
        self._run([])
        now = datetime.now(TZ)
        rc, out = self._run(["--agent-result",
                             json.dumps(self._healthy_payload(now))])
        self.assertEqual(rc, 0)
        self.assertIn("Watchdog: all scheduled jobs healthy.", out)

    def test_problem_result_logs(self):
        self._run([])
        now = datetime.now(TZ)
        payload = self._healthy_payload(now)
        for e in payload["jobs"]:
            if e["id"] == "repo-pull":
                e["runs"] = [{"at": at(now - timedelta(hours=40)),
                              "status": "completed", "error": None}]
        rc, out = self._run(["--agent-result", json.dumps(payload)])
        self.assertEqual(rc, 0)
        self.assertIn("repo-pull", out)
        self.assertIn("missed run", out)
        mem = os.path.join(self.tmp, "memory",
                           now.date().isoformat() + ".md")
        self.assertTrue(os.path.exists(mem))

    def test_invalid_rounds_fail_loudly(self):
        self._run([])
        rc = 10
        for _ in range(4):
            rc, _ = self._run(["--agent-result", json.dumps({})])
            self.assertEqual(rc, 10)
        rc, out = self._run(["--agent-result", json.dumps({})])
        self.assertEqual(rc, 20)


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
