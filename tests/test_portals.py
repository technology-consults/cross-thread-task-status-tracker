#!/usr/bin/env python3
"""
Portal & website regression suite.
Checks every live portal/website serves correctly.
Run: python3 tests/test_portals.py
Exit 0 = all pass, non-zero = failures (do NOT deploy).
"""
import sys, urllib.request

passed, failed = [], []

def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(f"{'PASS' if cond else 'FAIL'}: {name}" + (f" — {detail}" if detail and not cond else ""))

def fetch(url, timeout=20, retries=3):
    import time, subprocess
    last = None
    for i in range(retries):
        try:
            r = subprocess.run(["curl", "-s", "--max-time", str(timeout), "-w", "\n%{http_code}",
                                "-A", "muse-regression", url],
                               capture_output=True, timeout=timeout+5)
            out = r.stdout
            # split body from status code (last line)
            lines = out.rsplit(b"\n", 1)
            if len(lines) == 2:
                body, code = lines
                return int(code), body
            raise Exception("no status code")
        except Exception as e:
            last = e
            time.sleep(2)
    raise last

def fetch_nofollow(url, timeout=20):
    import subprocess
    r = subprocess.run(["curl", "-s", "-o", "/dev/null", "--max-time", str(timeout),
                        "-w", "%{http_code} %{redirect_url}", "-A", "muse-regression", url],
                       capture_output=True, timeout=timeout+5)
    parts = r.stdout.decode().split(" ", 1)
    return int(parts[0]), (parts[1] if len(parts) > 1 else "")

# --- bandhu-portal: dashboard home page (v1, BalRam 2026-09-30) ---
try:
    status, body = fetch("https://portal.technology-consults.workers.dev/")
    check("bandhu-portal: dashboard serves 200", status == 200, f"got {status}")
    check("bandhu-portal: dashboard is HTML", b"<html" in body[:500].lower())
    check("bandhu-portal: dashboard shows program status", b"Program status" in body)
    check("bandhu-portal: dashboard has hamburger menu", b"menu-btn" in body and b'id="drawer"' in body)
    check("bandhu-portal: dashboard has milestones", b'id="dashboard"' in body and b"Milestones" in body)
    check("bandhu-portal: dashboard version is v1", b">v1<" in body)
    check("bandhu-portal: no canonical /p/ links in dashboard", b'href="/p/' not in body and b"href='/p/" not in body)
    status2, body2 = fetch("https://portal.technology-consults.workers.dev/docs")
    check("bandhu-portal: /docs serves 200", status2 == 200, f"got {status2}")
    check("bandhu-portal: /docs shows documentation index", b"Documentation Index" in body2)
except Exception as e:
    for n in ["bandhu-portal: dashboard serves 200", "bandhu-portal: dashboard is HTML",
              "bandhu-portal: dashboard shows program status", "bandhu-portal: dashboard has hamburger menu",
              "bandhu-portal: dashboard has milestones", "bandhu-portal: dashboard version is v1",
              "bandhu-portal: no canonical /p/ links in dashboard",
              "bandhu-portal: /docs serves 200", "bandhu-portal: /docs shows documentation index"]:
        check(n, False, str(e)[:100])

# --- bandhu-portal: board (canonical /board) ---
try:
    status, body = fetch("https://portal.technology-consults.workers.dev/board")
    check("bandhu-portal: /board serves 200", status == 200, f"got {status}")
    check("bandhu-portal: board has 14-status model", b"pending_review" in body)
    check("bandhu-portal: board CSS linked", b"board.css" in body)
except Exception as e:
    check("bandhu-portal: /board serves 200", False, str(e)[:100])
    check("bandhu-portal: board has 14-status model", False, "fetch failed")
    check("bandhu-portal: board CSS linked", False, "fetch failed")

# --- bandhu-portal: board CSS ---
try:
    status, body = fetch("https://portal.technology-consults.workers.dev/assets/board.css")
    check("bandhu-portal: board.css serves 200", status == 200, f"got {status}")
    check("bandhu-portal: board.css has thead fix", b"thead" in body)
except Exception as e:
    check("bandhu-portal: board.css serves 200", False, str(e)[:100])
    check("bandhu-portal: board.css has thead fix", False, "fetch failed")

# --- bandhu-portal: tasks.json ---
try:
    status, body = fetch("https://portal.technology-consults.workers.dev/tasks.json")
    check("bandhu-portal: tasks.json serves 200", status == 200, f"got {status}")
    import json
    d = json.loads(body)
    check("bandhu-portal: tasks.json valid JSON with tasks", "tasks" in d and len(d["tasks"]) > 0)
except Exception as e:
    check("bandhu-portal: tasks.json serves 200", False, str(e)[:100])
    check("bandhu-portal: tasks.json valid JSON with tasks", False, "fetch/parse failed")

# --- bandhu-portal: retired /p/* redirects ---
try:
    s, loc = fetch_nofollow("https://portal.technology-consults.workers.dev/p/board")
    check("bandhu-portal: /p/board redirects to /board", s == 302 and loc.endswith("/board"), f"{s} -> {loc}")
    s, loc = fetch_nofollow("https://portal.technology-consults.workers.dev/p/")
    check("bandhu-portal: /p/ redirects to /", s == 302 and loc.endswith("/"), f"{s} -> {loc}")
    s, loc = fetch_nofollow("https://portal.technology-consults.workers.dev/p/ev-deals/")
    check("bandhu-portal: /p/ev-deals/ redirects to GitHub Pages",
          s == 302 and loc == "https://technology-consults.github.io/vehicle/ev-deals/", f"{s} -> {loc}")
    s, loc = fetch_nofollow("https://portal.technology-consults.workers.dev/p/artifacts/")
    check("bandhu-portal: /p/artifacts/ redirects to /", s == 302 and loc.endswith("/") and "#" not in loc, f"{s} -> {loc}")
except Exception as e:
    for n in ["bandhu-portal: /p/board redirects to /board",
              "bandhu-portal: /p/ redirects to /",
              "bandhu-portal: /p/ev-deals/ redirects to GitHub Pages",
              "bandhu-portal: /p/artifacts/ redirects to /"]:
        check(n, False, str(e)[:100])

# --- bandhu-portal: EV deals on GitHub Pages ---
try:
    status, body = fetch("https://technology-consults.github.io/vehicle/ev-deals/")
    check("vehicle-pages: ev-deals serves 200", status == 200, f"got {status}")
    check("vehicle-pages: ev-deals has newest-entry marker", b"NEWEST ENTRY GOES DIRECTLY BELOW THIS LINE" in body)
except Exception as e:
    check("vehicle-pages: ev-deals serves 200", False, str(e)[:100])
    check("vehicle-pages: ev-deals has newest-entry marker", False, "fetch failed")

# --- trading-portal: etf-live.html (GitHub Pages) ---
try:
    status, body = fetch("https://technology-consults.github.io/trading-portal/etf-live.html")
    check("trading-portal: etf-live.html serves 200", status == 200, f"got {status}")
    check("trading-portal: etf-live has bundle marker", b"__BUNDLE_START__" in body)
    check("trading-portal: etf-live has QQQ/SPY/GLD", all(s in body for s in [b"QQQ", b"SPY", b"GLD"]))
except Exception as e:
    check("trading-portal: etf-live.html serves 200", False, str(e)[:100])
    check("trading-portal: etf-live has bundle marker", False, "fetch failed")
    check("trading-portal: etf-live has QQQ/SPY/GLD", False, "fetch failed")

print(f"\n{len(passed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
