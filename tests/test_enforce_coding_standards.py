#!/usr/bin/env python3
"""Unit tests for scripts/enforce/coding_standards.py.

Convention: a main() printing "<N> passed, <M> failed", exit 0 on
success, 1 on failure.

Every trigger payload is built by string concatenation so this file's
own added lines never trip the gates it tests.
"""
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MOD_PATH = os.path.join(REPO_ROOT, "scripts", "enforce",
                        "coding_standards.py")

spec = importlib.util.spec_from_file_location("coding_standards_mod",
                                              MOD_PATH)
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


def mdiff(files):
    """{path: (is_new, [(lineno, line), ...])} -> the module's diff dict."""
    return {"files": {p: {"is_new": n, "added": a}
                      for p, (n, a) in files.items()}}


# --- py-compile --------------------------------------------------------------

def test_py_compile_good():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "good.py"), "w") as f:
            f.write("def f():\n    return 1\n")
        diff = mdiff({"good.py": (True, [(1, "def f():")])})
        check("py-compile: good file passes",
              mod.check_py_compile(diff, d, set()) == [])


def test_py_compile_bad():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "bad.py"), "w") as f:
            f.write("def broken(:\n")
        diff = mdiff({"bad.py": (True, [(1, "def broken(:")])})
        out = mod.check_py_compile(diff, d, set())
        check("py-compile: syntax error blocked",
              len(out) == 1 and out[0][0] == "py-compile"
              and out[0][1] == "bad.py")


def test_py_compile_deleted_skipped():
    with tempfile.TemporaryDirectory() as d:
        diff = mdiff({"gone.py": (False, [])})
        check("py-compile: deleted file skipped",
              mod.check_py_compile(diff, d, set()) == [])


def test_py_compile_writes_no_cache():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "x.py"), "w") as f:
            f.write("X = 1\n")
        diff = mdiff({"x.py": (True, [(1, "X = 1")])})
        mod.check_py_compile(diff, d, set())
        check("py-compile: writes no cache files",
              not os.path.exists(os.path.join(d, "__pycache__")))


# --- dangerous-calls ---------------------------------------------------------

def test_dangerous_calls():
    cases = [
        ("ev" + "al(", "eval"),
        ("ex" + "ec(", "exec"),
        ("os.sys" + "tem(", "os.system"),
        ("x = 1; " + "shell" + "=True", "subprocess shell"),
        ("pickle.lo" + "ads(data)", "pickle.loads"),
        ("d = " + "yaml." + "load(" + "f)", "unsafe yaml.load"),
    ]
    for payload, label in cases:
        diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
        out = mod.check_dangerous(diff, REPO_ROOT, set())
        check("dangerous-calls: %s blocked" % label,
              len(out) == 1 and out[0][0] == "dangerous-calls")


def test_dangerous_calls_safe_passes():
    safe = [
        "d = " + "yaml." + "load(" + "f, Loader=SafeLoader)",
        "subprocess.run(['ls'], shell=False)",
        "evaluation = compute(x)",
        "executor.submit(fn)",
    ]
    for payload in safe:
        diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
        check("dangerous-calls: safe line passes: %s" % payload[:30],
              mod.check_dangerous(diff, REPO_ROOT, set()) == [])


def test_dangerous_calls_non_python_skipped():
    diff = mdiff({"notes.md": (False, [(1, "ev" + "al(")])})
    check("dangerous-calls: non-.py skipped",
          mod.check_dangerous(diff, REPO_ROOT, set()) == [])


def test_dangerous_calls_allowlist():
    diff = mdiff({"scripts/legacy.py": (False, [(1, "ev" + "al(")])})
    check("dangerous-calls: allowlisted path exempt",
          mod.check_dangerous(diff, REPO_ROOT,
                              {"scripts/legacy.py"}) == [])


# --- bare-except -------------------------------------------------------------

def test_bare_except():
    diff = mdiff({"scripts/x.py": (False, [(3, "except" + ":")])})
    out = mod.check_bare_except(diff, REPO_ROOT, set())
    check("bare-except: bare except blocked",
          len(out) == 1 and out[0][0] == "bare-except")


def test_bare_except_named_passes():
    diff = mdiff({"scripts/x.py":
                  (False, [(3, "except ValueError:")])})
    check("bare-except: named except passes",
          mod.check_bare_except(diff, REPO_ROOT, set()) == [])


# --- no-cache ----------------------------------------------------------------

def test_no_cache():
    diff = mdiff({"scripts/__pycache__/x.pyc": (True, [])})
    out = mod.check_no_cache(diff, REPO_ROOT, set())
    check("no-cache: cache path blocked",
          len(out) == 1 and out[0][0] == "no-cache")


def test_no_cache_clean_passes():
    diff = mdiff({"scripts/x.py": (True, [(1, "X = 1")])})
    check("no-cache: normal path passes",
          mod.check_no_cache(diff, REPO_ROOT, set()) == [])


# --- tests-with-code ---------------------------------------------------------

def test_tests_with_code():
    diff = mdiff({"scripts/new_tool.py":
                  (True, [(1, "def run():"), (2, "    pass")])})
    out = mod.check_tests_with_code(diff, REPO_ROOT, set())
    check("tests-with-code: new def without test blocked",
          len(out) == 1 and out[0][0] == "tests-with-code")


def test_tests_with_code_satisfied():
    diff = mdiff({"scripts/new_tool.py": (True, [(1, "def run():")]),
                  "tests/test_new_tool.py": (True, [(1, "X = 1")])})
    check("tests-with-code: test file in diff satisfies",
          mod.check_tests_with_code(diff, REPO_ROOT, set()) == [])


def test_tests_with_code_test_file_exempt():
    diff = mdiff({"tests/test_x.py": (True, [(1, "def helper():")])})
    check("tests-with-code: test files never trigger",
          mod.check_tests_with_code(diff, REPO_ROOT, set()) == [])


def test_tests_with_code_non_code_dir():
    diff = mdiff({"docs/note.py": (True, [(1, "def f():")])})
    check("tests-with-code: non-code dir does not trigger",
          mod.check_tests_with_code(diff, REPO_ROOT, set()) == [])


def test_tests_with_code_src_dir():
    diff = mdiff({"src/crons/job/main.py": (True, [(1, "class Job:")])})
    out = mod.check_tests_with_code(diff, REPO_ROOT, set())
    check("tests-with-code: src/ counts as a code dir",
          len(out) == 1 and out[0][0] == "tests-with-code")


def main():
    test_py_compile_good()
    test_py_compile_bad()
    test_py_compile_deleted_skipped()
    test_py_compile_writes_no_cache()
    test_dangerous_calls()
    test_dangerous_calls_safe_passes()
    test_dangerous_calls_non_python_skipped()
    test_dangerous_calls_allowlist()
    test_bare_except()
    test_bare_except_named_passes()
    test_no_cache()
    test_no_cache_clean_passes()
    test_tests_with_code()
    test_tests_with_code_satisfied()
    test_tests_with_code_test_file_exempt()
    test_tests_with_code_non_code_dir()
    test_tests_with_code_src_dir()
    print("%d passed, %d failed" % (_passed, _failed))
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
