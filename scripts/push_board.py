#!/usr/bin/env python3
"""Push board files to the cross-thread-task-status-tracker repo via GitHub API."""
import base64, json, sys, urllib.request, urllib.error
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

REPO = "technology-consults/cross-thread-task-status-tracker"
BUILD = "/home/hatch/workspace/board-build"

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

def put_file(path, local, message, sha=None):
    with open(local, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    body = {"message": message, "content": content, "branch": "main"}
    if sha:
        body["sha"] = sha
    r = api("PUT", f"/repos/{REPO}/contents/{path}", body)
    print(f"PUT {path}: {r.get('commit', {}).get('sha', '')[:8]} {r.get('commit', {}).get('message', '')}")

def main():
    # current sha of index.html
    cur = api("GET", f"/repos/{REPO}/contents/index.html")
    put_file("index.html", f"{BUILD}/index.html",
             "Board v2: priorities, overdue/blocked, task IDs, deps, next-dues, thread views", sha=cur["sha"])
    # tasks.json: new or update
    try:
        cur2 = api("GET", f"/repos/{REPO}/contents/tasks.json")
        sha2 = cur2["sha"]
    except SystemExit:
        sha2 = None
    put_file("tasks.json", f"{BUILD}/tasks.json",
             "Board v2 task dataset (52 items, source of truth)", sha=sha2)

if __name__ == "__main__":
    main()
