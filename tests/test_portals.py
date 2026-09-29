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

# --- bandhu-portal: main hub ---
try:
    status, body = fetch("https://portal.technology-consults.workers.dev/")
    check("bandhu-portal: hub serves 200", status == 200, f"got {status}")
    check("bandhu-portal: hub is HTML", b"<html" in body[:500].lower())
except Exception as e:
    check("bandhu-portal: hub serves 200", False, str(e)[:100])
    check("bandhu-portal: hub is HTML", False, "fetch failed")

# --- bandhu-portal: board ---
try:
    status, body = fetch("https://portal.technology-consults.workers.dev/p/board")
    check("bandhu-portal: /p/board serves 200", status == 200, f"got {status}")
    check("bandhu-portal: board has 14-status model", b"pending_review" in body)
    check("bandhu-portal: board CSS linked", b"board.css" in body)
except Exception as e:
    check("bandhu-portal: /p/board serves 200", False, str(e)[:100])
    check("bandhu-portal: board has 14-status model", False, "fetch failed")
    check("bandhu-portal: board CSS linked", False, "fetch failed")

# --- bandhu-portal: board CSS ---
try:
    status, body = fetch("https://portal.technology-consults.workers.dev/p/assets/board.css")
    check("bandhu-portal: board.css serves 200", status == 200, f"got {status}")
    check("bandhu-portal: board.css has thead fix", b"thead" in body)
except Exception as e:
    check("bandhu-portal: board.css serves 200", False, str(e)[:100])
    check("bandhu-portal: board.css has thead fix", False, "fetch failed")

# --- bandhu-portal: tasks.json ---
try:
    status, body = fetch("https://portal.technology-consults.workers.dev/p/tasks.json")
    check("bandhu-portal: tasks.json serves 200", status == 200, f"got {status}")
    import json
    d = json.loads(body)
    check("bandhu-portal: tasks.json valid JSON with tasks", "tasks" in d and len(d["tasks"]) > 0)
except Exception as e:
    check("bandhu-portal: tasks.json serves 200", False, str(e)[:100])
    check("bandhu-portal: tasks.json valid JSON with tasks", False, "fetch/parse failed")

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
