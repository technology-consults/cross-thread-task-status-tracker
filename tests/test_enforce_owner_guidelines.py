#!/usr/bin/env python3
"""Unit tests for scripts/enforce/owner_guidelines.py.

Convention: a main() printing "<N> passed, <M> failed", exit 0 on
success, 1 on failure.

Every trigger payload is built by string concatenation so this file's
own added lines never trip the gates it tests.
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(HERE)
MOD_PATH = os.path.join(REPO_ROOT, "scripts", "enforce",
                        "owner_guidelines.py")

spec = importlib.util.spec_from_file_location("owner_guidelines_mod",
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


# --- platform-cli ------------------------------------------------------------

def test_platform_cli():
    payload = "run(" + chr(34) + "insta" + "gram-cli" + " post" + chr(34) + ")"
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    out = mod.check_platform_cli(diff, REPO_ROOT, set())
    check("platform-cli: CLI mention blocked",
          len(out) == 1 and out[0][0] == "platform-cli")


def test_platform_cli_bare_name_passes():
    diff = mdiff({"scripts/x.py": (False, [(1, "post to instagram")])})
    check("platform-cli: bare platform name passes",
          mod.check_platform_cli(diff, REPO_ROOT, set()) == [])


def test_platform_cli_allowlist():
    payload = "x(" + chr(34) + "you" + "tube-cli" + chr(34) + ")"
    diff = mdiff({"scripts/legacy.py": (False, [(1, payload)])})
    check("platform-cli: allowlisted path exempt",
          mod.check_platform_cli(diff, REPO_ROOT,
                                 {"scripts/legacy.py"}) == [])


# --- docs-home ---------------------------------------------------------------

def test_docs_home():
    diff = mdiff({"docs/stray.md": (True, [(1, "# hi")])})
    out = mod.check_docs_home(diff, REPO_ROOT, set())
    check("docs-home: new md outside docs/technical blocked",
          len(out) == 1 and out[0][0] == "docs-home")


def test_docs_home_technical_passes():
    diff = mdiff({"docs/technical/plan.md": (True, [(1, "# hi")])})
    check("docs-home: new md under docs/technical passes",
          mod.check_docs_home(diff, REPO_ROOT, set()) == [])


def test_docs_home_existing_grandfathered():
    diff = mdiff({"docs/stray.md": (False, [(1, "more")])})
    check("docs-home: existing misplaced doc not flagged",
          mod.check_docs_home(diff, REPO_ROOT, set()) == [])


# --- pdf-naming --------------------------------------------------------------

def test_pdf_naming():
    diff = mdiff({"docs/report.pdf": (True, [])})
    out = mod.check_pdf_naming(diff, REPO_ROOT, set())
    check("pdf-naming: stray PDF blocked",
          len(out) == 1 and out[0][0] == "pdf-naming")


def test_pdf_naming_combined_passes():
    name = "docs/cross-thread-task-status-tracker-documentation.pdf"
    diff = mdiff({name: (True, [])})
    check("pdf-naming: combined documentation PDF passes",
          mod.check_pdf_naming(diff, REPO_ROOT, set()) == [])


# --- portability-row ---------------------------------------------------------

def test_portability_row():
    payload = "sys.path.insert(0, " + chr(34) + "/op" + "t/hatch/bin" + chr(34) + ")"
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    out = mod.check_portability_row(diff, REPO_ROOT, set())
    check("portability-row: runtime dep without notes row blocked",
          len(out) == 1 and out[0][0] == "portability-row")


def test_portability_row_satisfied():
    payload = "sys.path.insert(0, " + chr(34) + "/op" + "t/hatch/bin" + chr(34) + ")"
    diff = mdiff({"scripts/x.py": (False, [(1, payload)]),
                  "docs/technical/portability-notes.md": (False, [(1, "row")])})
    check("portability-row: notes file in diff satisfies",
          mod.check_portability_row(diff, REPO_ROOT, set()) == [])


def test_portability_row_test_exempt():
    payload = "p = " + chr(34) + "/op" + "t/hatch/x" + chr(34)
    diff = mdiff({"tests/test_x.py": (False, [(1, payload)])})
    check("portability-row: test files exempt",
          mod.check_portability_row(diff, REPO_ROOT, set()) == [])


# --- no-git-push -------------------------------------------------------------

def test_no_git_push():
    payload = ("o" + "s.system(" + chr(34) + "git" + " push origin main"
               + chr(34) + ")")
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    out = mod.check_no_git_push(diff, REPO_ROOT, set())
    check("no-git-push: push via the git command blocked",
          len(out) == 1 and out[0][0] == "no-git-push")


def test_no_git_push_docs_skipped():
    payload = "never run " + chr(34) + "git" + " push" + chr(34) + " here"
    diff = mdiff({"docs/note.md": (False, [(1, payload)])})
    check("no-git-push: only .py/.sh scanned",
          mod.check_no_git_push(diff, REPO_ROOT, set()) == [])


# --- no-raw-github -----------------------------------------------------------

def _needle():
    return "raw." + "githubusercontent.com"


def test_no_raw_github():
    payload = "url = 'https://" + _needle() + "/o/r/main/f.py'"
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    out = mod.check_no_raw_github(diff, REPO_ROOT, set())
    ok = (len(out) == 1 and out[0][0] == "no-raw-github"
          and "api.github.com" in out[0][3])
    check("no-raw-github: raw CDN fetch blocked, api.github.com named", ok)


def test_no_raw_github_api_passes():
    payload = ("url = 'https://api.github.com/repos/o/r/contents/f.py"
               "?ref=main'")
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    check("no-raw-github: api.github.com URL passes",
          mod.check_no_raw_github(diff, REPO_ROOT, set()) == [])


def test_no_raw_github_allowlist():
    payload = "url = 'https://" + _needle() + "/o/r/main/f.py'"
    diff = mdiff({"scripts/x.py": (False, [(1, payload)])})
    check("no-raw-github: allowlisted path exempt",
          mod.check_no_raw_github(diff, REPO_ROOT,
                                  {"scripts/x.py"}) == [])


def main():
    test_platform_cli()
    test_platform_cli_bare_name_passes()
    test_platform_cli_allowlist()
    test_docs_home()
    test_docs_home_technical_passes()
    test_docs_home_existing_grandfathered()
    test_pdf_naming()
    test_pdf_naming_combined_passes()
    test_portability_row()
    test_portability_row_satisfied()
    test_portability_row_test_exempt()
    test_no_git_push()
    test_no_git_push_docs_skipped()
    test_no_raw_github()
    test_no_raw_github_api_passes()
    test_no_raw_github_allowlist()
    print("%d passed, %d failed" % (_passed, _failed))
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
