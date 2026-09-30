#!/usr/bin/env python3
"""Unit tests for scripts/enforce/remediation.py and the no-bypass rule.

Convention: a main() printing "<N> passed, <M> failed", exit 0 on
success, 1 on failure.
"""
import importlib.util
import io
import os
import sys
from contextlib import redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MOD_PATH = os.path.join(REPO_ROOT, "scripts", "enforce", "remediation.py")

spec = importlib.util.spec_from_file_location("remediation_mod", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
    else:
        _failed += 1
        print("FAIL: %s" % name)


def test_report_prints_protocol():
    buf = io.StringIO()
    with redirect_stderr(buf):
        mod.report([("no-cache", "x.pyc", 0, "cache")])
    out = buf.getvalue()
    check("remediation: report names the violation",
          "BLOCKED [no-cache]" in out)
    check("remediation: report prints the protocol",
          "GATE FAILURE" in out and "No silent bypass" in out)


def test_task_templates_critical():
    mine, approval = mod.task_templates(
        "secrets", "scripts/x.py", 3, "sk-...", "board write blocked",
        "sv", critical=True)
    check("remediation: critical approval is prod-critical + hourly",
          approval.get("priority") == "prod-critical"
          and approval.get("poke") == "hourly")
    check("remediation: my task blocked on the approval task",
          mine["status"] == "blocked"
          and approval["id"] in mine["blockedBy"])
    check("remediation: thread carried into task ids",
          mine["id"].startswith("sv.") and approval["id"].startswith("sv."))
    check("remediation: approval assigned to the owner",
          approval["assigned_to"] == "BalRam")


def test_task_templates_non_critical():
    mine, approval = mod.task_templates(
        "secrets", "scripts/x.py", 3, "sk-...", "docs typo", "tr",
        critical=False)
    check("remediation: non-critical approval has no priority/poke",
          "priority" not in approval and "poke" not in approval)
    check("remediation: non-critical still blocks my task",
          mine["status"] == "blocked")


def test_rule_change_templates():
    mine, agreement = mod.rule_change_templates(
        "docs-home", "allow docs/blog/", "blog lives here", "vh")
    check("remediation: rule change pair blocked on agreement",
          mine["status"] == "blocked"
          and agreement["id"] in mine["blockedBy"])
    check("remediation: agreement rides the normal review stream",
          agreement["status"] == "pending_review"
          and "priority" not in agreement and "poke" not in agreement)


def test_no_bypass_flag_in_commit():
    with open(os.path.join(REPO_ROOT, "scripts", "commit.py"),
              encoding="utf-8") as f:
        src = f.read()
    check("remediation: commit.py offers no bypass flag",
          "--force" not in src and "--no-verify" not in src)
    check("remediation: protocol states there is no --force",
          "--force" in mod.PROTOCOL_TEXT
          and "Never bypass silently" in mod.PROTOCOL_TEXT)


def main():
    test_report_prints_protocol()
    test_task_templates_critical()
    test_task_templates_non_critical()
    test_rule_change_templates()
    test_no_bypass_flag_in_commit()
    print("%d passed, %d failed" % (_passed, _failed))
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
