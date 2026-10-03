#!/usr/bin/env python3
"""Unit tests for push_board.py board-version check (pure helpers only --
no network).

The board shows meta.boardVersion (semver, e.g. 1.0.0) top-right, read
live with the data. Bump it on every board change.

Convention: a main() printing "<N> passed, <M> failed", exit 0 on
success, 1 on failure.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MOD_PATH = os.path.join(REPO_ROOT, "push_board.py")

spec = importlib.util.spec_from_file_location("push_board_mod", MOD_PATH)
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


def test_valid_version_passes():
    check("push_board: valid semver passes",
          mod.check_board_version({"meta": {"boardVersion": "1.0.0"}}) is None)
    check("push_board: multi-digit semver passes",
          mod.check_board_version({"meta": {"boardVersion": "12.3.45"}}) is None)


def test_missing_version_fails():
    check("push_board: missing meta fails",
          mod.check_board_version({}) is not None)
    check("push_board: missing boardVersion fails",
          mod.check_board_version({"meta": {}}) is not None)


def test_malformed_version_fails():
    for bad in ("1.0", "v1.0.0", "1.0.0-beta", "", 123, None):
        check("push_board: malformed version %r fails" % (bad,),
              mod.check_board_version({"meta": {"boardVersion": bad}}) is not None)


def main():
    test_valid_version_passes()
    test_missing_version_fails()
    test_malformed_version_fails()
    print("%d passed, %d failed" % (_passed, _failed))
    sys.exit(1 if _failed else 0)


if __name__ == "__main__":
    main()
