#!/usr/bin/env python3
"""Pre-commit owner-guideline gates for the cross-thread-task-status-tracker.

The owner's standing rules that are mechanically checkable on a commit
diff live here as code. Reads a diff on stdin as JSON:
    {"files": {"<repo-rel path>": {"is_new": bool,
                                   "added": [[lineno, line], ...]}}}
argv[1] is the repo root.

Prints one line per violation:
    BLOCKED [<gate>] <path>:<lineno>: <snippet>
Exit 0 when clean, 1 on violations, 2 on usage/internal error.

Gates are documented on GATE_DEFS below; scripts/enforce/gates.json
mirrors that registry and a unit test enforces the match. Stdlib only.

Each gate's deliberate-act escape is its allowlist file. Entries are
exact repo-relative paths or directory prefixes ending in "/". A missing
allowlist file fails closed (exempts nothing).
"""
import json
import os
import re
import sys

# ---------------------------------------------------------------------------
# Gate registry: (name, one-line description, allowlist relpath or None).
# ---------------------------------------------------------------------------
GATE_DEFS = [
    ("platform-cli",
     "platform CLI mentions in added lines; use the native API instead",
     "scripts/enforce/allowlist_cli.txt"),
    ("docs-home",
     "new markdown under docs/ belongs under docs/technical/",
     "scripts/enforce/allowlist_docs_home.txt"),
    ("pdf-naming",
     "committed PDFs are the single combined <project>-documentation.pdf",
     "scripts/enforce/allowlist_pdfs.txt"),
    ("portability-row",
     "a new Muse-runtime dependency needs a portability-notes.md row "
     "in the same diff",
     "scripts/enforce/allowlist_portability.txt"),
    ("no-git-push",
     "no pushing via git in scripts: GitHub is API-only",
     "scripts/enforce/allowlist_gitops.txt"),
    ("no-raw-github",
     "no raw-file CDN fetches: all GitHub reads go through api.github.com",
     "scripts/enforce/allowlist_rawgithub.txt"),
]

ENFORCE_DIR = os.path.dirname(os.path.abspath(__file__))
PORTABILITY_NOTES = "docs/technical/portability-notes.md"

# Platform CLI names, WITHOUT the "-cli" suffix on purpose: the gate checks
# for name + "-cli" in each added line, and storing the bare names keeps
# this file's own added lines from tripping the gate it implements.
# The owner's standing rule bans every platform CLI, everywhere.
CLI_NAMES = ("instagram", "facebook", "threads", "youtube", "tiktok", "x")

# Markers of a Muse-runtime-only dependency. Built at runtime so this
# source never carries the literals the portability gate scans for.
def _runtime_markers():
    return ("/home" + "/hatch",
            "/opt" + "/hatch",
            "~" + "/workspace",
            "dynamic_" + "credentials")

# Matches a push invoked through the git command in added script lines.
# Built at runtime for the same reason: this module's own added lines
# must never trip the gate it implements.
def _push_pattern():
    return re.compile(r"\bgit\s+push\b")

_PY_SH = (".py", ".sh")


def load_allowlist(repo_root, rel):
    """Set of exempt paths/prefixes; empty (fail closed) when unavailable."""
    if not rel:
        return set()
    try:
        with open(os.path.join(repo_root, rel), encoding="utf-8") as f:
            return {ln.strip() for ln in f
                    if ln.strip() and not ln.strip().startswith("#")}
    except OSError:
        print("warning: allowlist %s missing; no exemptions" % rel,
              file=sys.stderr)
        return set()


def is_exempt(path, allow):
    if path in allow:
        return True
    return any(path.startswith(p) for p in allow if p.endswith("/"))


def _is_test_path(path):
    return ("/tests/" in path or path.startswith("tests/")
            or os.path.basename(path).startswith("test_"))


# --- gates -----------------------------------------------------------------

def check_platform_cli(diff, repo_root, allow):
    """Block platform-CLI mentions in added lines."""
    out = []
    for path, info in diff["files"].items():
        if is_exempt(path, allow):
            continue
        for lineno, line in info["added"]:
            low = line.lower()
            for name in CLI_NAMES:
                if name + "-cli" in low:
                    out.append(("platform-cli", path, lineno,
                                line.strip()[:120]))
                    break
    return out


def check_docs_home(diff, repo_root, allow):
    """New markdown under docs/ belongs under docs/technical/.

    Only new paths are flagged; existing misplaced docs are grandfathered.
    """
    out = []
    for path, info in diff["files"].items():
        if not info["is_new"] or not path.endswith(".md"):
            continue
        if not path.startswith("docs/") or path.startswith("docs/technical/"):
            continue
        if not is_exempt(path, allow):
            out.append(("docs-home", path, 0, path[:120]))
    return out


def check_pdf_naming(diff, repo_root, allow):
    """Committed PDFs are the single combined <project>-documentation.pdf.

    Standing rule: one combined documentation PDF per repo, never one
    PDF per page.
    """
    out = []
    for path in diff["files"]:
        if not path.lower().endswith(".pdf"):
            continue
        if os.path.basename(path).endswith("-documentation.pdf"):
            continue
        if not is_exempt(path, allow):
            out.append(("pdf-naming", path, 0, path[:120]))
    return out


def check_portability_row(diff, repo_root, allow):
    """A new Muse-runtime dependency needs a portability-notes.md row.

    If any added non-test Python line introduces a runtime marker, the
    same diff must touch docs/technical/portability-notes.md (the
    deliberate act). Test files are exempt: fixtures may name such paths.
    """
    markers = _runtime_markers()
    flagged = []
    for path, info in diff["files"].items():
        if not path.endswith(".py") or is_exempt(path, allow):
            continue
        if _is_test_path(path):
            continue
        for lineno, line in info["added"]:
            if any(m in line for m in markers):
                flagged.append((path, lineno, line.strip()[:120]))
                break  # one flag per file is enough signal
    if not flagged:
        return []
    if PORTABILITY_NOTES in diff["files"]:
        return []
    return [("portability-row", p, n, s) for p, n, s in flagged]


def check_no_git_push(diff, repo_root, allow):
    """No pushing via git in scripts: GitHub is API-only, ever.

    The local clones have no push credentials; every write goes through
    the GitHub API (contents API / git trees API).
    """
    push_re = _push_pattern()
    out = []
    for path, info in diff["files"].items():
        if not path.endswith(_PY_SH) or is_exempt(path, allow):
            continue
        for lineno, line in info["added"]:
            if push_re.search(line):
                out.append(("no-git-push", path, lineno,
                            line.strip()[:120]))
                break  # one flag per file is enough signal
    return out


def _raw_github_needle():
    # The banned host, built at runtime so this module's own source never
    # carries the literal the gate scans for (same trick as the
    # portability gate's runtime markers).
    return "raw." + "githubusercontent.com"


def check_no_raw_github(diff, repo_root, allow):
    """GitHub is API-only: committed code must never fetch from the raw
    file CDN (owner's rule 2026-09-30 -- it triggers a phone approval
    prompt). All GitHub reads go through api.github.com: the contents
    API for files, the git trees API, and the tarball endpoint for
    archives. The violation message names the api.github.com
    equivalent. (Complements the whole-tree scanner at
    scripts/enforce/no_raw_githubusercontent.py, which audits committed
    files rather than diffs.)"""
    needle = _raw_github_needle()
    out = []
    for path, info in diff["files"].items():
        if is_exempt(path, allow):
            continue
        for lineno, line in info["added"]:
            if needle in line:
                msg = ("%s is banned -- GitHub is API-only (2026-09-30). "
                       "Use the contents API "
                       "(https://api.github.com/repos/{owner}/{repo}/"
                       "contents/{path}) or the tarball endpoint "
                       "(https://api.github.com/repos/{owner}/{repo}/"
                       "tarball/{sha}) instead: %s"
                       % (needle, line.strip()[:80]))
                out.append(("no-raw-github", path, lineno, msg))
                break  # one flag per file is enough signal
    return out


# --- entry point -------------------------------------------------------------

_CHECKS = {
    "platform-cli": check_platform_cli,
    "docs-home": check_docs_home,
    "pdf-naming": check_pdf_naming,
    "portability-row": check_portability_row,
    "no-git-push": check_no_git_push,
    "no-raw-github": check_no_raw_github,
}


def check_all(diff, repo_root):
    allowlists = {name: load_allowlist(repo_root, rel)
                  for name, _desc, rel in GATE_DEFS}
    out = []
    for name, _desc, _rel in GATE_DEFS:
        out.extend(_CHECKS[name](diff, repo_root, allowlists[name]))
    return out


def read_diff():
    try:
        raw = sys.stdin.read()
    except OSError as e:
        print("error: cannot read stdin: %s" % e, file=sys.stderr)
        sys.exit(2)
    try:
        diff = json.loads(raw)
    except ValueError as e:
        print("error: invalid diff JSON: %s" % e, file=sys.stderr)
        sys.exit(2)
    if not isinstance(diff, dict) or "files" not in diff:
        print("error: diff JSON needs a 'files' object", file=sys.stderr)
        sys.exit(2)
    return diff


def main(argv):
    if len(argv) != 2:
        print("usage: %s <repo-root> < diff.json" % argv[0], file=sys.stderr)
        return 2
    violations = check_all(read_diff(), argv[1])
    for gate, path, lineno, snippet in violations:
        print("BLOCKED [%s] %s:%d: %s" % (gate, path, lineno, snippet))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
