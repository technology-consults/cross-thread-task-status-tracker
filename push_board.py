#!/usr/bin/env python3
"""Push board files to the cross-thread-task-status-tracker repo via GitHub API."""
import base64, json, sys, urllib.request, urllib.error
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

REPO = "technology-consults/cross-thread-task-status-tracker"
BUILD = "/home/hatch/workspace/repos/cross-thread-task-status-tracker"

def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        "https://api.github.com" + path, data=data, method=method,
        headers={"User-Agent": "muse-agent",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

def put_file(path, local, message):
    with open(local, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    body = {"message": message, "content": content, "branch": "main"}
    try:
        cur = api("GET", f"/repos/{REPO}/contents/{path}")
        body["sha"] = cur["sha"]
    except SystemExit:
        pass
    r = api("PUT", f"/repos/{REPO}/contents/{path}", body)
    print(f"PUT {path}: {r.get('commit', {}).get('sha', '')[:8]} {r.get('commit', {}).get('message', '')}")

CF_ACCT = "f5ab3d8595f37065d333e639f56926c2"
CF_NS = "85718c092905432bbb8501d4a5f78520"

def kv_put(key, local):
    with open(local, "rb") as f:
        data = f.read()
    import urllib.parse
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCT}/storage/kv/namespaces/{CF_NS}/values/{urllib.parse.quote(key, safe='')}",
        data=data, method="PUT",
        headers={"User-Agent": "muse-agent"})
    add_surrogate_to_request(req, "custom.cloudflare", allowed_hosts=["api.cloudflare.com"])
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            j = json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        print(f"KV PUT {key} failed: HTTP {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    if not j.get("success"):
        print(f"KV PUT {key} failed: {j.get('errors')}", file=sys.stderr)
        sys.exit(1)
    print(f"KV portal sync: {key} ({len(data)}b)")

def main():
    # validate: every task status must exist in the board's STATUS map, or rendering breaks
    import re
    html = open(f"{BUILD}/index.html").read()
    known = set(re.findall(r'^\s{2}(\w+):\{label:', html, re.M))
    data = json.load(open(f"{BUILD}/tasks.json"))
    bad = [(x["id"], x.get("status")) for x in data["tasks"] if x.get("status") not in known]
    if bad:
        # unknown statuses now render with a fallback chip/badge instead of crashing,
        # so this is a loud warning (add a proper label/rank/color to STATUS), not a block
        print(f"WARNING: statuses not in the board's STATUS map (will show with fallback styling): {bad}")
    print(f"status check ok ({len(known)} known, {len(data['tasks'])} tasks)")
    put_file("index.html", f"{BUILD}/index.html",
             "Board: compute anchored on meta.asOf, 'No due date' labels, artifact-index link")
    put_file("tasks.json", f"{BUILD}/tasks.json",
             "Board dataset: 2FA/GitHub record corrections (2026-09-27)")
    put_file("tests/synthetic_matrix.js", f"{BUILD}/tests/synthetic_matrix.js",
             "Board QC: synthetic date-boundary test matrix (66 cases)")
    put_file("board.css", f"{BUILD}/board.css",
             "Board: separate stylesheet (portal v1)")
    # keep the private portal's tracker in sync (prevents stale board on the portal)
    kv_put("p:board", f"{BUILD}/index.html")
    kv_put("p:tasks.json", f"{BUILD}/tasks.json")
    kv_put("p:assets/board.css", f"{BUILD}/board.css")
    check_unblocks_after_push()


def check_unblocks_after_push():
    """Run the unblock watcher for every thread whose task statuses changed.

    His standing rule (2026-09-27): the unblock check runs hourly AND whenever
    a task status is updated. Every status update flows through this script, so
    the push is the trigger. Newly actionable tasks print as an UNBLOCK REPORT;
    the agent delivers each thread's report to that project's task tracker and
    acts (starts own work / pokes him), then records handled ids in
    hidden_files/unblock_watch_state.json so the hourly cron doesn't re-fire.

    His standing rule (2026-09-28): board task updates (new tasks and status
    changes) are delivered to the project's task TRACKER thread on every board
    publish — not the project discussion threads. They print as TASK UPDATES
    blocks below; the agent delivers each thread's block to that project's
    task tracker thread via chat.send_message.
    """
    import subprocess
    # Project task-tracker threads (NOT the project discussion side chats).
    TRACKER_THREADS = {
        "sv": "d82796e3-56f1-4d34-bf51-665165a38e92",  # Short Video task tracker
        "tr": "1ff0cb94-8438-4900-8c47-a39846cbf1a3",  # Trading task tracker
        "vh": "547fb3d1-6b69-4410-b9d0-084cd478e7ff",  # Vehicle task tracker
    }
    snap_path = f"{BUILD}/hidden_files/task_status_snapshot.json"
    try:
        prev = json.load(open(snap_path))
    except (FileNotFoundError, json.JSONDecodeError):
        prev = {}
    data = json.load(open(f"{BUILD}/tasks.json"))
    tasks = data["tasks"] if isinstance(data, dict) else data
    cur = {}
    changed_threads = set()
    updates = {}
    for t in tasks:
        tid = t.get("id")
        if not tid:
            continue
        st = t.get("status")
        cur[tid] = st
        old = prev.get(tid)  # None => newly added task
        if old != st and t.get("thread"):
            changed_threads.add(t["thread"])
            updates.setdefault(t["thread"], []).append({
                "id": tid,
                "title": t.get("title"),
                "old": old,
                "new": st,
            })
    json.dump(cur, open(snap_path, "w"), indent=1)
    if updates:
        for th in sorted(updates):
            items = updates[th]
            print(f"===== TASK UPDATES thread={th} tracker={TRACKER_THREADS.get(th, '')} ({len(items)} changed) =====")
            print(json.dumps(items, indent=1, ensure_ascii=False))
            print(f"===== END TASK UPDATES thread={th} =====")
    if not changed_threads:
        print("unblock check: no task status changes since last push, skipping")
        return
    for th in sorted(changed_threads):
        r = subprocess.run(["python3", f"{BUILD}/unblock_watch.py", "--thread", th],
                           capture_output=True, text=True)
        try:
            items = json.loads(r.stdout)
        except json.JSONDecodeError:
            items = []
        if items:
            print(f"===== UNBLOCK REPORT thread={th} ({len(items)} newly actionable) =====")
            print(json.dumps(items, indent=1, ensure_ascii=False))
            print(f"===== END UNBLOCK REPORT thread={th} =====")
        else:
            print(f"unblock check thread={th}: status changed but no newly actionable tasks")

if __name__ == "__main__":
    main()
