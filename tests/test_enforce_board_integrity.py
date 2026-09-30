#!/usr/bin/env python3
"""Unit tests for scripts/enforce/board_integrity.py.

Convention: a main() printing "<N> passed, <M> failed", exit 0 on
success, 1 on failure.
"""
import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MOD_PATH = os.path.join(REPO_ROOT, "scripts", "enforce",
                        "board_integrity.py")

spec = importlib.util.spec_from_file_location("board_integrity_mod",
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


INDEX_HTML = """<html><body><script>
const STATUS = {
  todo: 1,
  done: 1
};
</script></body></html>
"""


def good_task(**kw):
    task = {"id": "sv.x", "thread": "sv", "title": "T",
            "status": "todo", "updated": "2026-09-30",
            "detail": "d"}
    task.update(kw)
    return task


def run_with(tasks_json_text, diff):
    """Run the gate with a temp repo root holding tasks.json+index.html."""
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "tasks.json"), "w") as f:
            f.write(tasks_json_text)
        with open(os.path.join(d, "index.html"), "w") as f:
            f.write(INDEX_HTML)
        return mod.check_tasks_schema(diff, d, set())


def board_text(tasks):
    return json.dumps({"meta": {}, "threads": {"sv": {}}, "tasks": tasks})


def test_not_in_diff_skipped():
    diff = mdiff({"scripts/x.py": (False, [(1, "X = 1")])})
    check("tasks-schema: tasks.json absent from diff -> no check",
          mod.check_tasks_schema(diff, REPO_ROOT, set()) == [])


def test_valid_board_passes():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([good_task()]), diff)
    check("tasks-schema: valid board passes", out == [])


def test_invalid_json():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with("{not json", diff)
    check("tasks-schema: invalid JSON blocked",
          len(out) == 1 and out[0][0] == "tasks-schema")


def test_tasks_not_list():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(json.dumps({"threads": {}, "tasks": {}}), diff)
    check("tasks-schema: non-list tasks blocked",
          any(v[0] == "tasks-schema" for v in out))


def test_empty_tasks():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([]), diff)
    check("tasks-schema: board wipe blocked",
          any(v[0] == "tasks-schema" for v in out))


def test_missing_required_field():
    task = good_task()
    del task["detail"]
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([task]), diff)
    check("tasks-schema: missing required field blocked",
          any(v[0] == "tasks-schema" and "detail" in v[3] for v in out))


def test_duplicate_ids():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([good_task(), good_task()]), diff)
    check("tasks-schema: duplicate ids blocked",
          any(v[0] == "tasks-schema" and "duplicate" in v[3]
              for v in out))


def test_unknown_status():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([good_task(status="flying")]), diff)
    check("tasks-schema: unknown status blocked",
          any(v[0] == "tasks-schema" and "status" in v[3] for v in out))


def test_unknown_thread():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([good_task(thread="nope")]), diff)
    check("tasks-schema: unknown thread blocked",
          any(v[0] == "tasks-schema" and "thread" in v[3] for v in out))


def test_malformed_blocked_by():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([good_task(blockedBy=[{"x": 1}])]), diff)
    check("tasks-schema: malformed blockedBy blocked",
          any(v[0] == "tasks-schema" and "blockedBy" in v[3]
              for v in out))


def test_blocked_by_string_ok():
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([good_task(blockedBy="sv.y")]), diff)
    check("tasks-schema: string blockedBy passes", out == [])


def test_optional_fields_ok():
    task = good_task(due=None, where="here", assigned_to="Bandhu",
                     priority="prod-critical", blockedBy=["sv.y"])
    diff = mdiff({"tasks.json": (False, [(1, "{")])})
    out = run_with(board_text([task]), diff)
    check("tasks-schema: optional fields pass", out == [])


def test_allowlist_exempts():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "tasks.json"), "w") as f:
            f.write("{not json")
        diff = mdiff({"tasks.json": (False, [(1, "{")])})
        out = mod.check_tasks_schema(diff, d, {"tasks.json"})
        check("tasks-schema: allowlisted tasks.json exempt", out == [])


def main():
    test_not_in_diff_skipped()
    test_valid_board_passes()
    test_invalid_json()
    test_tasks_not_list()
    test_empty_tasks()
    test_missing_required_field()
    test_duplicate_ids()
    test_unknown_status()
    test_unknown_thread()
    test_malformed_blocked_by()
    test_blocked_by_string_ok()
    test_optional_fields_ok()
    test_allowlist_exempts()
    print("%d passed, %d failed" % (_passed, _failed))
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
