#!/usr/bin/env python3
"""Enforce: no raw.githubusercontent.com URLs in committed code.

Standing rule (2026-09-30, BalRam): fetching raw.githubusercontent.com is
banned -- it is the same violation as using the browser for GitHub (it
triggered a phone approval prompt). ALL GitHub reads go through
api.github.com only.

This check scans files for raw.githubusercontent.com URLs and fails
(exit 1) on any hit, pointing at the api.github.com equivalent:

  raw:  https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>
  api:  https://api.github.com/repos/<owner>/<repo>/contents/<path>?ref=<ref>
        (base64-decoded "content" field; tarball endpoint for archives:
         https://api.github.com/repos/<owner>/<repo>/tarball/<sha>)

Usage:
    python3 scripts/enforce/no_raw_githubusercontent.py [path ...]
    # no paths -> scan the whole repo tree (excluding .git)

Exit 0 = clean. Exit 1 = violation found (lists file:line for each).
"""
import os
import re
import sys

RAW_RE = re.compile(r"https?://raw\.githubusercontent\.com/[^\s\"'<>]+")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(REPO_ROOT)  # scripts/enforce -> repo root

# The enforcer and its own tests are exempt: they name the banned domain to
# describe the ban and to fixture-test it, but contain no code that fetches
# it. Everything else is scanned.
SELF_EXEMPT = {
    os.path.normpath(os.path.join(REPO_ROOT, "scripts", "enforce",
                                  "no_raw_githubusercontent.py")),
    os.path.normpath(os.path.join(REPO_ROOT, "tests",
                                  "test_enforce_no_raw.py")),
}

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf",
             ".zip", ".gz", ".tar", ".mp4", ".mov"}


def api_equivalent(url):
    """Suggest the api.github.com equivalent for a raw URL, best-effort."""
    m = re.match(
        r"https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)",
        url)
    if not m:
        return ("use the api.github.com contents API instead of "
                "raw.githubusercontent.com")
    owner, repo, ref, path = m.groups()
    return ("https://api.github.com/repos/%s/%s/contents/%s?ref=%s "
            "(base64 content field)" % (owner, repo, path, ref))


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
        elif os.path.isdir(p):
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = sorted(
                    d for d in dirnames if d not in SKIP_DIRS)
                for fn in sorted(filenames):
                    if os.path.splitext(fn)[1].lower() in SKIP_EXTS:
                        continue
                    yield os.path.join(dirpath, fn)


def check_file(path):
    """Return list of (lineno, url) hits in one file."""
    hits = []
    try:
        with open(path, encoding="utf-8", errors="strict") as f:
            for lineno, line in enumerate(f, 1):
                for m in RAW_RE.finditer(line):
                    hits.append((lineno, m.group(0)))
    except (OSError, UnicodeError):
        pass  # unreadable/binary: skip (extension filter caught most)
    return hits


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    roots = args or [REPO_ROOT]
    violations = []
    for path in iter_files(roots):
        if os.path.normpath(path) in SELF_EXEMPT:
            continue
        for lineno, url in check_file(path):
            violations.append((path, lineno, url))
    if violations:
        print("ENFORCE FAIL: raw.githubusercontent.com URLs are banned "
              "(2026-09-30 standing rule).", file=sys.stderr)
        for path, lineno, url in violations:
            rel = os.path.relpath(path, REPO_ROOT)
            print("  %s:%d: %s" % (rel, lineno, url), file=sys.stderr)
            print("    -> use instead: %s" % api_equivalent(url),
                  file=sys.stderr)
        print("All GitHub reads go through api.github.com only: contents "
              "API for files, git trees API, tarball endpoint for archives.",
              file=sys.stderr)
        return 1
    print("ENFORCE OK: no raw.githubusercontent.com URLs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
