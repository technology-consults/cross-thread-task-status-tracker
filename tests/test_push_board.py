#!/usr/bin/env python3
"""Unit tests for push_board.py build-version stamping (pure helpers only --
no network).

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


def test_stamp_replaces_placeholder():
    out = mod.stamp_build_sha(
        b'<span class="ver" id="buildVer">__BUILD_SHA__</span>', "c587ec0")
    check("push_board: placeholder replaced with SHA",
          out == b'<span class="ver" id="buildVer">c587ec0</span>')


def test_stamp_no_placeholder_unchanged():
    data = b"<html>no marker here</html>"
    check("push_board: bytes without placeholder unchanged",
          mod.stamp_build_sha(data, "c587ec0") == data)


def test_stamp_keeps_rest_of_file():
    data = b"AAA__BUILD_SHA__BBB__BUILD_SHA__CCC"
    check("push_board: all occurrences stamped, rest intact",
          mod.stamp_build_sha(data, "c587ec0") == b"AAAc587ec0BBBc587ec0CCC")


def test_placeholder_constant():
    check("push_board: placeholder constant is the agreed marker",
          mod.BUILD_SHA_PLACEHOLDER == "__BUILD_SHA__")


def main():
    test_stamp_replaces_placeholder()
    test_stamp_no_placeholder_unchanged()
    test_stamp_keeps_rest_of_file()
    test_placeholder_constant()
    print("%d passed, %d failed" % (_passed, _failed))
    sys.exit(1 if _failed else 0)


if __name__ == "__main__":
    main()
