#!/usr/bin/env python3
"""Unit tests for scripts/commit.py (pure helpers only -- no network).

Convention: a main() printing "<N> passed, <M> failed", exit 0 on
success, 1 on failure.
"""
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MOD_PATH = os.path.join(REPO_ROOT, "scripts", "commit.py")

spec = importlib.util.spec_from_file_location("commit_mod", MOD_PATH)
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


def test_diff_added_new_file():
    out = mod.diff_added(None, ["a", "b"])
    check("commit: new file -> every line added",
          out == [(1, "a"), (2, "b")])


def test_diff_added_modified():
    out = mod.diff_added("a\nb\n", ["a", "B", "c"])
    check("commit: modified file -> only added lines",
          out == [(2, "B"), (3, "c")])


def test_diff_added_unchanged():
    out = mod.diff_added("a\n", ["a"])
    check("commit: unchanged file -> no added lines", out == [])


def test_load_ruleset_version():
    check("commit: ruleset version loads and is semver",
          mod.load_ruleset_version() == "1.0.0"
          and bool(re.match(r"^\d+\.\d+\.\d+$",
                            mod.load_ruleset_version())))


def test_blocked_line_parsing():
    m = mod._BLOCKED_RE.match("BLOCKED [no-cache] x.pyc:0: cache")
    check("commit: BLOCKED line parses",
          m is not None and m.group(1) == "no-cache"
          and m.group(2) == "x.pyc" and int(m.group(3)) == 0)


def test_enforce_modules_tuple():
    check("commit: enforce modules in fixed order",
          mod.ENFORCE_MODULES == ("coding_standards", "security",
                                  "owner_guidelines", "board_integrity"))


def main():
    test_diff_added_new_file()
    test_diff_added_modified()
    test_diff_added_unchanged()
    test_load_ruleset_version()
    test_blocked_line_parsing()
    test_enforce_modules_tuple()
    print("%d passed, %d failed" % (_passed, _failed))
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
