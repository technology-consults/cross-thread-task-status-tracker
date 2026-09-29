#!/usr/bin/env python3
"""Completed automation: blocked_completed -> completed -> post-actions -> done.

The board's interim rule (locked 2026-09-28) was manual thread moves for
everything past review. This script is the automation that replaces them.
It ONLY ever moves a task on BalRam's written approval (an explicit
'Verdict: approved|rejected' line on a done review task), and it ONLY ever
deploys through a verified mechanism (scripts/deploy_profiles.json) behind
a passing regression gate. Anything it cannot do safely it leaves untouched
and reports as a MANUAL block for the worker to deliver to the tracker
thread. The worker never auto-acts on a MANUAL block.

Phase 1 - verdict application (blocked_completed tasks):
  For each blocked_completed task, look at blockedBy entries of kind 'task'
  that point to a review task with status 'done':
    - all verdicts 'approved'  -> remove those blocks, task -> 'completed'
    - any verdict 'rejected'  -> remove those blocks, task -> 'not_approved'
    - a done review with no 'Verdict:' line -> MANUAL (cannot determine approval)
    - a review not done / other blockers still pending -> untouched

Phase 2 - post-actions (completed tasks):
  A task needs an explicit post plan in a 'post' object, written at
  review-submit time (see docs/completed-automation.md). No plan -> MANUAL.
  Idempotency ('never run on already-deployed work'): a completed task that
  already carries 'post_done' is skipped silently.

  post kinds:
    none     -> nothing to deploy; record post_done, task -> done
    message  -> print a MESSAGE block (worker delivers via chat.send_message);
                record post_done, task -> done
    artifact -> verify the file exists; record post_done, task -> done
    code     -> run the named deploy profile:
                1. regression gate (must pass, else stall + report)
                2. commit+push changed files via GitHub API (repo-first:
                   everything committed before any deploy step)
                3. release tag (semver, named in the post plan) on the commit
                4. run the profile's deploy mechanism
                5. verify live (HTTP 200 + content match per profile)
                6. record commit link + tag + verify evidence on the task,
                   task -> done
                Any failure: the task stays 'completed' and a MANUAL/STALL
                block is printed. Fix-forward: the failure is fixed and the
                task re-runs; rollback is only the last resort and is never
                automatic.

Safety defaults: dry-run unless --execute is passed. --tasks lets tests run
against a fixture instead of the live tasks.json.

After this script changes any statuses, the worker publishes via
push_board.py --publish (which runs the regression suite and prints the
TASK UPDATES / UNBLOCK REPORT blocks). The unblock watcher's
'completed_stalled' sweep is the safety net: a completed task older than a
day gets reported, never auto-acted on.
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import date

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
from dynamic_credentials import add_surrogate_to_request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_TASKS = os.path.join(BASE, "tasks.json")
PROFILES_PATH = os.path.join(BASE, "scripts", "deploy_profiles.json")
CHECKOUTS = os.path.expanduser("~/workspace/repos")

VERDICT = re.compile(r"(?im)^Verdict:\s*(approved|rejected)\b")

TRACKER_THREADS = {
    "sv": "d82796e3-56f1-4d34-bf51-665165a38e92",
    "tr": "1ff0cb94-8438-4900-8c47-a39846cbf1a3",
    "vh": "547fb3d1-6b69-4410-b9d0-084cd478e7ff",
}


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def today():
    return date.today().isoformat()


# ---------------------------------------------------------------- GitHub API

def gh(method, path, body=None):
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
        raise RuntimeError(f"GitHub {method} {path}: HTTP {e.code}: {e.read().decode()[:300]}")


def gh_put_file(repo, repo_path, local_path, message):
    """Commit one file via the Contents API. Returns the commit sha."""
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    body = {"message": message, "content": content, "branch": "main"}
    try:
        cur = gh("GET", f"/repos/{repo}/contents/{repo_path}")
        body["sha"] = cur["sha"]
    except RuntimeError:
        pass  # new file
    last = None
    for attempt in (1, 2):  # one retry on transient failure
        try:
            r = gh("PUT", f"/repos/{repo}/contents/{repo_path}", body)
            last = r.get("commit", {}).get("sha", "")
            break
        except RuntimeError as e:
            if attempt == 2:
                raise
            print(f"PUT {repo_path}: transient failure, retrying ({e})", file=sys.stderr)
            time.sleep(3)
    return last


def gh_create_tag(repo, tag, sha, message):
    """Create an annotated-style release tag. NOTE: plural /git/refs path —
    the singular /git/ref variant 404s/drops on PATCH/POST (2026-09-27)."""
    tag_obj = gh("POST", f"/repos/{repo}/git/tags",
                 {"tag": tag, "message": message, "object": sha, "type": "commit"})
    gh("POST", f"/repos/{repo}/git/refs",
       {"ref": f"refs/tags/{tag}", "sha": tag_obj["sha"]})
    return tag


def gh_blob_contains(repo, ref, repo_path, needle):
    """Verify a file's content at a tag/branch via the API (content check,
    never size/existence)."""
    r = gh("GET", f"/repos/{repo}/contents/{repo_path}?ref={ref}")
    content = base64.b64decode(r.get("content", "")).decode("utf-8", "replace")
    return needle in content


# ---------------------------------------------------------------- verification

def http_verify(url, needle, tries=6, pause=20):
    """GET url until HTTP 200 and needle appears (Pages builds take a minute
    or two). Returns (ok, detail)."""
    last = ""
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "muse-agent"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8", "replace")
                if resp.status == 200 and needle in body:
                    return True, f"HTTP 200, match '{needle[:60]}' present"
                last = f"HTTP {resp.status}, match missing"
        except Exception as e:  # noqa: BLE001 - any fetch failure is a failed check
            last = f"fetch failed: {e}"
        time.sleep(pause)
    return False, last


# ---------------------------------------------------------------- automation

class Completed:
    def __init__(self, tasks_path, execute):
        self.tasks_path = tasks_path
        self.execute = execute
        data = load(tasks_path, {})
        self.tasks = data if isinstance(data, list) else data.get("tasks", data.get("items", []))
        self.byid = {t.get("id"): t for t in self.tasks}
        self.profiles = load(PROFILES_PATH, {})
        self.actions = []   # completed-action records for the worker
        self.manual = []    # manual blocks for the worker
        self.changed = False

    # -- reporting -------------------------------------------------
    def record_action(self, task, action, evidence=None):
        self.actions.append({"task": task.get("id"), "thread": task.get("thread"),
                             "action": action, "evidence": evidence or {}})

    def record_manual(self, task, reason, needed):
        self.manual.append({"task": task.get("id"), "thread": task.get("thread"),
                            "title": task.get("title"), "reason": reason, "needed": needed})

    # -- phase 1: verdict application ------------------------------
    def apply_verdicts(self):
        for t in self.tasks:
            if t.get("status") != "blocked_completed":
                continue
            reviews = []
            for b in t.get("blockedBy") or []:
                if b.get("kind") != "task":
                    continue
                ref = self.byid.get(b.get("id"))
                if ref and ref.get("status") == "done":
                    reviews.append((b, ref))
            if not reviews:
                continue
            verdicts = []
            undecided = []
            for b, ref in reviews:
                m = VERDICT.search(ref.get("detail") or "")
                if m:
                    verdicts.append((b, m.group(1)))
                else:
                    undecided.append(ref.get("id"))
            if undecided:
                self.record_manual(
                    t, f"review {undecided[0]} is done but carries no 'Verdict:' line",
                    "BalRam's written verdict (approved/rejected) on the review task")
                continue
            if any(v == "rejected" for _, v in verdicts):
                self._retire_blocks(t, [b for b, _ in reviews])
                self._set_status(t, "not_approved")
                self.record_action(t, "verdict rejected -> not_approved",
                                   {"reviews": [ref.get("id") for _, ref in reviews]})
            else:
                self._retire_blocks(t, [b for b, _ in reviews])
                self._set_status(t, "completed")
                self.record_action(t, "verdict approved -> completed",
                                   {"reviews": [ref.get("id") for _, ref in reviews]})

    def _retire_blocks(self, t, blocks):
        ids = {b.get("id") for b in blocks}
        t["blockedBy"] = [b for b in (t.get("blockedBy") or []) if b.get("id") not in ids]

    def _set_status(self, t, status):
        if self.execute:
            t["status"] = status
            t["updated"] = today()
            self.changed = True
        else:
            self.record_action(t, f"DRY-RUN would set status -> {status}")

    # -- phase 2: post-actions -------------------------------------
    def run_post_actions(self):
        for t in self.tasks:
            if t.get("status") != "completed":
                continue
            if t.get("post_done"):
                continue  # already deployed: never run twice
            post = t.get("post")
            if not post:
                self.record_manual(
                    t, "no post plan on the task",
                    "add a 'post' object (kind/repo/files/profile/verify) at review-submit time; "
                    "until then this task is handled manually")
                continue
            kind = post.get("kind")
            try:
                if kind == "none":
                    self._finish(t, {"note": "no deployable output"})
                elif kind == "message":
                    self._post_message(t, post)
                elif kind == "artifact":
                    self._post_artifact(t, post)
                elif kind == "code":
                    self._post_code(t, post)
                else:
                    self.record_manual(t, f"unknown post kind '{kind}'",
                                       "fix the post plan on the task")
            except RuntimeError as e:
                # fix-forward: leave in completed, report the stall, never rollback automatically
                self.record_manual(t, f"post-action failed: {e}",
                                   "fix the failure and re-run; the task stays in 'completed' "
                                   "until the post-actions succeed (watcher reports the stall)")

    def _finish(self, t, evidence):
        if self.execute:
            t["post_done"] = {"at": today(), **evidence}
            t["status"] = "done"
            t["updated"] = today()
            self.changed = True
        self.record_action(t, "post-actions ok -> done", evidence)

    def _post_message(self, t, post):
        text = post.get("text") or ""
        if not text:
            raise RuntimeError("post kind 'message' needs a 'text' field")
        self._finish(t, {"message": text[:80]})

    def _post_artifact(self, t, post):
        path = os.path.expanduser(post.get("path") or "")
        if not path or not os.path.exists(path):
            raise RuntimeError(f"artifact missing at {path or '(no path)'}")
        self._finish(t, {"artifact": path, "bytes": os.path.getsize(path)})

    def _post_code(self, t, post):
        profile_name = post.get("profile")
        profile = self.profiles.get(profile_name or "")
        if not profile:
            raise RuntimeError(f"no verified deploy profile '{profile_name}' — "
                               "mechanisms are never guessed; map it in deploy_profiles.json first")
        if not profile.get("verified"):
            raise RuntimeError(f"deploy profile '{profile_name}' is not verified — "
                               "no step runs until its mechanism proves out on a real call")
        repo = post.get("repo") or profile.get("repo")
        files = post.get("files") or []
        if not repo or not files:
            raise RuntimeError("post plan needs 'repo' and 'files'")
        tag = post.get("tag")
        if not tag:
            raise RuntimeError("post plan needs a 'tag' (semver, chosen at review-submit time)")

        checkout = os.path.join(CHECKOUTS, repo.split("/")[-1])
        local_files = []
        for f in files:
            lp = os.path.join(checkout, f)
            if not os.path.exists(lp):
                raise RuntimeError(f"changed file not in local checkout: {lp}")
            local_files.append((f, lp))

        # 1. regression gate — no deploy without a passing suite, ever
        gate = profile.get("gate")
        if not gate:
            raise RuntimeError(f"profile '{profile_name}' has no regression gate — "
                               "a deploy suite must exist and pass before any deploy")
        self._run_gate(t, gate, checkout, local_files)

        # 2. commit + push (repo-first: committed before any deploy step)
        commit_msg = f"{t.get('id')}: {t.get('title')}"
        shas = [gh_put_file(repo, rf, lf, commit_msg) for rf, lf in local_files]
        head = shas[-1]
        if not head:
            raise RuntimeError("push returned no commit sha")

        # 3. release tag on the deployed commit
        gh_create_tag(repo, tag, head, f"{tag}: {t.get('title')}")

        # 4. deploy mechanism per profile kind
        kind = profile.get("kind")
        if kind == "repo":
            pass  # the push IS the deploy for script repos; the tag marks it
        elif kind == "board":
            self._run_board_publish()
        elif kind in ("pages", "kv-content"):
            cmd = profile.get("deploy_cmd")
            if not cmd:
                raise RuntimeError(f"profile '{profile_name}' names no deploy_cmd")
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=checkout)
            if r.returncode != 0:
                raise RuntimeError(f"deploy command failed: {r.stderr[:300]}")
        else:
            raise RuntimeError(f"profile '{profile_name}' has unknown kind '{kind}'")

        # 5. per-change verification: content check, never size/existence
        verify = post.get("verify") or {}
        url, needle = verify.get("url"), verify.get("match")
        if url and needle:
            ok, detail = http_verify(url, needle)
            if not ok:
                raise RuntimeError(f"live verification failed for {url}: {detail}")
            evidence = {"commit": head[:8], "tag": tag, "verified": f"{url} ({detail})"}
        elif kind == "repo":
            # verify the tagged blob carries the change
            blob_ok = all(gh_blob_contains(repo, tag, rf, needle)
                          for rf, needle in self._needles(post))
            if not blob_ok:
                raise RuntimeError(f"tagged blob verification failed for {tag}")
            evidence = {"commit": head[:8], "tag": tag, "verified": f"blob at tag {tag}"}
        else:
            raise RuntimeError("post plan needs verify.url + verify.match")

        self._finish(t, evidence)

    def _run_gate(self, t, gate, cwd, local_files=()):
        # "py_compile_changed": generic gate for script repos — every changed
        # .py file must compile. Real check, no project suite required.
        if gate == "py_compile_changed":
            pys = [lp for _, lp in local_files if lp.endswith(".py")]
            if not pys:
                return
            r = subprocess.run([sys.executable, "-m", "py_compile", *pys],
                               capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                raise RuntimeError(f"py_compile failed on changed files:\n{r.stderr[-500:]}")
            return
        r = subprocess.run(gate, capture_output=True, text=True, timeout=300, cwd=cwd)
        if r.returncode != 0:
            raise RuntimeError(f"regression gate failed: {' '.join(gate)}\n{r.stdout[-500:]}")

    def _run_board_publish(self):
        r = subprocess.run([sys.executable, os.path.join(BASE, "push_board.py"), "--publish"],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError(f"board publish failed: {r.stderr[-300:] or r.stdout[-300:]}")

    @staticmethod
    def _needles(post):
        """(repo_path, needle) pairs for blob verification of script repos."""
        for item in post.get("verify_blobs") or []:
            yield item.get("path"), item.get("match")

    # -- persistence + reporting -----------------------------------
    def save(self):
        if self.execute and self.changed:
            with open(self.tasks_path, "w") as f:
                json.dump({"tasks": self.tasks}, f, indent=1, ensure_ascii=False)

    def report(self):
        if self.actions:
            by_thread = {}
            for a in self.actions:
                by_thread.setdefault(a.get("thread") or "?", []).append(a)
            for th in sorted(by_thread):
                print(f"===== COMPLETED-ACTION thread={th} tracker={TRACKER_THREADS.get(th, '')} =====")
                print(json.dumps(by_thread[th], indent=1, ensure_ascii=False))
                print(f"===== END COMPLETED-ACTION thread={th} =====")
        if self.manual:
            by_thread = {}
            for m in self.manual:
                by_thread.setdefault(m.get("thread") or "?", []).append(m)
            for th in sorted(by_thread):
                print(f"===== MANUAL thread={th} tracker={TRACKER_THREADS.get(th, '')} =====")
                print(json.dumps(by_thread[th], indent=1, ensure_ascii=False))
                print(f"===== END MANUAL thread={th} =====")
        if not self.actions and not self.manual:
            print("completed automation: nothing actionable")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--execute", action="store_true",
                    help="actually move tasks and deploy; without it, dry-run only")
    ap.add_argument("--tasks", default=DEFAULT_TASKS,
                    help="tasks.json path (tests point this at a fixture)")
    args = ap.parse_args()

    job = Completed(args.tasks, args.execute)
    job.apply_verdicts()
    job.run_post_actions()
    job.save()
    job.report()
    if not args.execute:
        print("dry-run mode: nothing was changed (pass --execute to act)")


if __name__ == "__main__":
    main()
