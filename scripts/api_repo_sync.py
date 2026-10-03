#!/usr/bin/env python3
"""API fallback sync for workbench clones whose `git fetch` fails on auth.

A clone pointing at a private GitHub repo with no credentials makes
`git fetch` die with "could not read Username". This helper syncs the
working tree through the GitHub API instead, using this repo's established
API auth (the same `api()` helper `scripts/commit.py` uses).

Usage: python3 api_repo_sync.py <repo-dir> <name>
Prints exactly one status line, in pull_all_repos.sh vocabulary:
  OK <name>: already current (<sha>, verified via API - no fetch credentials)
  PULLED <name>: -> <sha> (working tree synced via API tarball)
  FAIL <name>: <error text>

Safety rules (all enforced, fail closed):
- The working tree must be clean (no `git status --porcelain` output
  outside `__pycache__`); otherwise refuse immediately.
- The remote is never touched. The sync commit is local-only and is
  never pushed (workbench clones never push, by standing rule).
- After staging the tarball content, the index tree SHA must equal the
  remote tree SHA from the API; on mismatch the index is reset and the
  run aborts without committing.
- The tarball is fully extracted and verified before anything in the
  working tree is touched.
"""

import base64
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")

API = "https://api.github.com"
AUTH_FAILURE_RE = re.compile(
    r"could not read username|authentication failed|permission denied"
    r"|repository not found|invalid username or password",
    re.IGNORECASE,
)
# owner/repo out of https://github.com/<owner>/<repo>(.git) or git@github.com:...
REMOTE_RE = re.compile(
    r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$")


def is_auth_failure(stderr_text):
    """True when git's stderr looks like a credentials/auth failure."""
    return bool(AUTH_FAILURE_RE.search(stderr_text or ""))


def parse_owner_repo(remote_url):
    """'https://github.com/o/r.git' -> ('o', 'r'); None when unparseable."""
    m = REMOTE_RE.search((remote_url or "").strip())
    if not m:
        return None
    return m.group("owner"), m.group("repo")


def api(method, path, body=None, raw=False):
    """GitHub API via the repo's established auth (token or surrogate)."""
    import json as _json
    from dynamic_credentials import add_surrogate_to_request
    data = _json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"User-Agent": "muse-agent",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    else:
        add_surrogate_to_request(req, "custom.github",
                                 allowed_hosts=["api.github.com"])
    with urllib.request.urlopen(req, timeout=120) as resp:
        payload = resp.read()
    if raw:
        return payload
    return _json.loads(payload.decode() or "{}")


def run_git(repo_dir, *args):
    r = subprocess.run(["git", "-C", repo_dir] + list(args),
                       capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def tree_is_clean(repo_dir):
    """Clean = no porcelain output outside __pycache__."""
    _, out, _ = run_git(repo_dir, "status", "--porcelain")
    lines = [ln for ln in out.splitlines() if "__pycache__" not in ln]
    return not lines


def remote_head(owner, repo):
    """(commit_sha, tree_sha) of origin/main via the API."""
    ref = api("GET", "/repos/%s/%s/git/ref/heads/main" % (owner, repo))
    commit_sha = ref["object"]["sha"]
    commit = api("GET", "/repos/%s/%s/git/commits/%s" % (owner, repo,
                                                         commit_sha))
    return commit_sha, commit["tree"]["sha"]


def local_tree_sha(repo_dir):
    rc, out, _ = run_git(repo_dir, "rev-parse", "HEAD^{tree}")
    return out if rc == 0 else None


def download_tarball(owner, repo, sha, dest_path):
    """Fetch the git archive tarball for a commit SHA via the API.

    Delegates to the shared toolkit's get_tarball (agent-tools/scripts/gh.py),
    which strips the Authorization header on the 302 redirect to the codeload
    host — replaying the credential there makes codeload answer 404.
    """
    sys.path.insert(0, os.path.join(REPO_ROOT, "..", "agent-tools",
                                    "scripts"))
    from gh import get_tarball as _get_tarball
    _get_tarball("%s/%s" % (owner, repo), sha, dest_path)


def sync_worktree_from_tarball(repo_dir, tarball_path):
    """Replace the working tree (minus .git) with the tarball content."""
    tmp = tempfile.mkdtemp(prefix="api-sync-")
    try:
        with tarfile.open(tarball_path, "r:gz") as tf:
            # Safety: refuse tarballs with absolute paths or .. escapes.
            for member in tf.getmembers():
                if member.name.startswith("/") or ".." in member.name.split("/"):
                    raise ValueError("unsafe tar member: %r" % member.name)
            tf.extractall(tmp)
        tops = [d for d in os.listdir(tmp)
                if os.path.isdir(os.path.join(tmp, d))]
        if len(tops) != 1:
            raise ValueError("expected one top-level dir, got %r" % tops)
        src = os.path.join(tmp, tops[0])
        # rsync the content over the worktree; .git and caches are kept.
        r = subprocess.run(
            ["rsync", "-a", "--delete",
             "--exclude", ".git/", "--exclude", "__pycache__/",
             src + "/", repo_dir + "/"],
            capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise RuntimeError("rsync failed: %s" % r.stderr.strip()[:200])
        # Drop regenerable bytecode caches: `git add -A` below must not
        # stage them, or the tree SHA will never match the remote tree.
        for _root, dirs, files in os.walk(repo_dir):
            if ".git" in dirs:
                dirs.remove(".git")
            for d in [d for d in dirs if d == "__pycache__"]:
                shutil.rmtree(os.path.join(_root, d), ignore_errors=True)
                dirs.remove(d)
            for f in files:
                if f.endswith((".pyc", ".pyo")):
                    os.unlink(os.path.join(_root, f))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def fail(name, reason):
    print("FAIL %s: %s" % (name, reason))
    return 1


def main(argv):
    if len(argv) != 3:
        print("usage: api_repo_sync.py <repo-dir> <name>")
        return 2
    repo_dir, name = argv[1], argv[2]

    if not tree_is_clean(repo_dir):
        return fail(name, "working tree has local changes; refusing API sync")

    _, remote_url, _ = run_git(repo_dir, "config", "--get",
                               "remote.origin.url")
    parsed = parse_owner_repo(remote_url)
    if not parsed:
        return fail(name, "cannot parse owner/repo from remote %r"
                    % remote_url)
    owner, repo = parsed

    try:
        commit_sha, remote_tree = remote_head(owner, repo)
    except Exception as e:  # noqa: BLE001 - report, don't crash
        return fail(name, "API error reading remote head: %s" % str(e)[:150])

    local_tree = local_tree_sha(repo_dir)
    if local_tree == remote_tree:
        print("OK %s: already current (%s, verified via API - "
              "no fetch credentials)" % (name, commit_sha[:8]))
        return 0

    # Behind: refresh the working tree from the API tarball, then make a
    # LOCAL-ONLY sync commit (never pushed; workbench clones never push).
    tmp_tar = None
    try:
        fd, tmp_tar = tempfile.mkstemp(prefix="api-sync-", suffix=".tgz")
        os.close(fd)
        download_tarball(owner, repo, commit_sha, tmp_tar)
        sync_worktree_from_tarball(repo_dir, tmp_tar)

        rc, _, err = run_git(repo_dir, "add", "-A")
        if rc != 0:
            raise RuntimeError("git add failed: %s" % err[:150])
        # The staged tree MUST equal the remote tree, else abort.
        rc, index_tree, err = run_git(repo_dir, "write-tree")
        if rc != 0 or index_tree != remote_tree:
            run_git(repo_dir, "reset", "-q")
            raise RuntimeError(
                "staged tree %s != remote tree %s; aborted"
                % (index_tree[:8] if index_tree else "?",
                   remote_tree[:8]))
        rc, _, err = run_git(
            repo_dir, "-c", "user.name=Bandhu",
            "-c", "user.email=bandhu@technology-consults",
            "commit", "-q", "-m",
            "sync: align working tree with GitHub main %s (via API tarball)"
            % commit_sha[:8])
        if rc != 0:
            run_git(repo_dir, "reset", "-q")
            raise RuntimeError("sync commit failed: %s" % err[:150])
    except Exception as e:  # noqa: BLE001 - report, don't crash
        return fail(name, str(e)[:200])
    finally:
        if tmp_tar and os.path.exists(tmp_tar):
            os.unlink(tmp_tar)

    print("PULLED %s: -> %s (working tree synced via API tarball)"
          % (name, commit_sha[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
