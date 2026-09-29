#!/usr/bin/env python3
"""
Board regression suite — ensures nothing existing breaks.
Run before every board deploy: python3 tests/regression.py
Exit 0 = all pass, non-zero = failures (do NOT deploy).
"""
import json, re, subprocess, sys, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

passed, failed = [], []

def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(f"{'PASS' if cond else 'FAIL'}: {name}" + (f" — {detail}" if detail and not cond else ""))

# --- 1. tasks.json: all statuses known ---
d = json.load(open("tasks.json"))
with open("index.html") as f:
    html = f.read()
m = re.search(r"const STATUS\s*=\s*\{(.*?)\n\};", html, re.DOTALL)
known = set(re.findall(r'^\s*(\w+):', m.group(1), re.MULTILINE)) if m else set()
unknown = {t["status"] for t in d["tasks"]} - known
check("tasks.json: all statuses known", not unknown, f"unknown: {unknown}")

# --- 2. tasks.json: required fields ---
req = {"id", "title", "status", "thread"}
missing = [t["id"] for t in d["tasks"] if not req <= set(t.keys())]
check("tasks.json: required fields present", not missing, f"missing: {missing[:3]}")

# --- 3. tasks.json: no duplicate ids ---
ids = [t["id"] for t in d["tasks"]]
check("tasks.json: no duplicate ids", len(ids) == len(set(ids)))

# --- 4. push_board.py: --help does not publish ---
r = subprocess.run([sys.executable, "push_board.py", "--help"],
                   capture_output=True, text=True, timeout=30)
check("push_board.py: --help exits 0 without publishing",
      r.returncode == 0 and "usage" in r.stdout.lower())

# --- 5. push_board.py: bare run is dry-run only ---
r = subprocess.run([sys.executable, "push_board.py"],
                   capture_output=True, text=True, timeout=60)
check("push_board.py: bare run validates (no --publish flag needed for dry-run)",
      "validation ok" in r.stdout or "dry" in r.stdout.lower())

# --- 6. board.css: digest header white on blue ---
css = open("board.css").read()
check("board.css: digest thead white on blue",
      ".digest-table thead th" in css and "color:#fff" in css.replace(" ", ""))

# --- 7. board.css: no halo strokes (cairosvg bug) ---
check("board.css: no paint-order halo strokes", "paint-order" not in css)

# --- 8. index.html: graceful unknown-status fallback ---
check("index.html: unknown status fallback",
      "unknown" in html.lower() and "STATUS" in html)

# --- 9. index.html: filter persistence ---
check("index.html: filter localStorage persistence", "boardFilters.v1" in html)

# --- 10. digest PDFs: generate without error ---
VENV_PY = os.path.expanduser("~/workspace/.docbuild-venv/bin/python")
if not os.path.exists(VENV_PY):
    VENV_PY = sys.executable
r = subprocess.run([VENV_PY, "scripts/pending_digest.py", "--thread", "sv"],
                   capture_output=True, text=True, timeout=60)
check("digest: sv PDFs generate",
      r.returncode == 0 and "PDF_PATH_DIGEST1" in r.stdout, r.stderr[:200])

# --- 11. digest PDFs: header textColor white in source ---
src = open("scripts/pending_digest.py").read()
check("digest: header paragraphs explicitly white",
      "textColor=colors.white" in src)

# --- 12. index.html: 14 statuses in STATUS map ---
check("index.html: 14 statuses defined", len(known) == 14, f"found {len(known)}")

print(f"\n{len(passed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
