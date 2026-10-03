#!/usr/bin/env python3
"""Workspace-to-git backup: ensure all work product is in git.

Single mechanism replacing commit-check, cron-definitions-sync, and
agent-working-files-backup. Scans workspace folders for code/docs/artifacts
(except videos) and ensures each is committed to GitHub:

  - Folder is a git clone with uncommitted changes -> commit via API.
  - Folder has work product but is not a git repo -> create GitHub repo,
    initialize local git, commit files, wire into repo-pull sync.

This is a BACKUP/SYNC job, not a code change: it commits files as-is via
the GitHub API. No gates apply (per standing rule, gates are for code
changes, not backup commits).

Usage: python3 workspace_to_git.py [--dry-run] [--json]

Config: FOLDER_MAP below defines workspace path -> GitHub repo. Folders not
in the map but containing work product get a repo named
technology-consults/workspace-<basename>.
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import time

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
from api_repo_sync import api  # noqa: E402

HOME = os.path.expanduser("~")
WORKSPACE = os.environ.get("WORKSPACE_DIR", os.path.join(HOME, "workspace"))
ORG = "technology-consults"

# Workspace path (relative to ~/workspace) -> GitHub repo name.
# Folders not listed here get technology-consults/workspace-<basename>.
FOLDER_MAP = {
    "prompts": "agent-tools",
    "_cron-work": "agent-tools",
    "repos/agent-tools": "agent-tools",
    "repos/bandhu-portal": "bandhu-portal",
    "repos/cross-thread-task-status-tracker": "cross-thread-task-status-tracker",
    "repos/short-video": "short-video",
    "repos/short-video-publisher": "short-video-publisher",
    "repos/trading": "trading",
    "repos/trading-portal": "trading-portal",
    "repos/vehicle": "vehicle",
    # Cron definitions -> tracker repo's crons/ directory (replaces
    # cron-definitions-sync). The sync_crons_to_git.py logic is preserved:
    # definitions are mirrored, not just committed in place.
    "cron.d": "cross-thread-task-status-tracker:crons",
    "system-cron.d": "cross-thread-task-status-tracker:crons",
}

# File extensions that count as "work product" (code, docs, configs).
WORK_EXTENSIONS = {
    ".py", ".js", ".ts", ".sh", ".md", ".json", ".yaml", ".yml",
    ".html", ".css", ".txt", ".toml", ".ini", ".cfg", ".xml",
}

# Never back up these.
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".pytest_cache", "node_modules",
    "archive", "browser_downloads", "disposable",
}
EXCLUDE_EXTENSIONS = {
    ".pyc", ".pyo", ".mp4", ".mov", ".avi", ".mkv", ".webm",
    ".mp3", ".wav", ".zip", ".tar", ".gz",
}


def is_work_product(path):
    """True if the file is code/docs/config (not video, cache, etc.)."""
    _, ext = os.path.splitext(path)
    if ext.lower() in EXCLUDE_EXTENSIONS:
        return False
    if ext.lower() in WORK_EXTENSIONS:
        return True
    # Extensionless scripts (e.g., run, deploy) count if executable.
    if not ext and os.access(path, os.X_OK):
        return True
    return False


def find_work_files(root):
    """All work-product files under root, excluding caches/archives."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded dirs in-place.
        dirnames[:] = [d for d in dirnames
                       if d not in EXCLUDE_DIRS and not d.endswith("-2026-")]
        # Skip hidden_files (run logs, state) — not work product.
        if "hidden_files" in dirpath:
            continue
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            if is_work_product(fp):
                found.append(fp)
    return found


def run_git(repo_dir, *args):
    r = subprocess.run(["git", "-C", repo_dir] + list(args),
                       capture_output=True, text=True, timeout=60)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def blob_sha(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def ensure_github_repo(repo_name, private=True):
    """Create the GitHub repo if it doesn't exist. Returns True if created."""
    try:
        api("GET", "/repos/%s/%s" % (ORG, repo_name))
        return False  # Already exists.
    except Exception:
        pass
    api("POST", "/orgs/%s/repos" % ORG, {
        "name": repo_name,
        "private": private,
        "auto_init": False,
        "description": "Workspace backup: %s (auto-created)" % repo_name,
    })
    return True


def commit_files_to_repo(repo_name, files, message):
    """Commit files to GitHub repo via Trees API (backup-style, no gates).

    files: list of (repo_path, local_path). Creates a single commit on main.
    """
    # Get current main SHA.
    try:
        ref = api("GET", "/repos/%s/%s/git/ref/heads/main" % (ORG, repo_name))
        base_sha = ref["object"]["sha"]
        base_commit = api("GET", "/repos/%s/%s/git/commits/%s"
                          % (ORG, repo_name, base_sha))
        base_tree = base_commit["tree"]["sha"]
    except Exception:
        # No main yet (new repo): start from empty tree.
        base_sha = None
        base_tree = None

    # Build tree entries.
    tree = []
    for repo_path, local_path in files:
        with open(local_path, "rb") as f:
            raw = f.read()
        blob = api("POST", "/repos/%s/%s/git/blobs" % (ORG, repo_name), {
            "content": base64.b64encode(raw).decode(),
            "encoding": "base64",
        })
        tree.append({"path": repo_path, "mode": "100644",
                     "type": "blob", "sha": blob["sha"]})

    tree_body = {"tree": tree}
    if base_tree:
        tree_body["base_tree"] = base_tree
    new_tree = api("POST", "/repos/%s/%s/git/trees" % (ORG, repo_name),
                   tree_body)

    commit_body = {"message": message, "tree": new_tree["sha"]}
    if base_sha:
        commit_body["parents"] = [base_sha]
    new_commit = api("POST", "/repos/%s/%s/git/commits" % (ORG, repo_name),
                     commit_body)

    if base_sha:
        api("PATCH", "/repos/%s/%s/git/ref/heads/main" % (ORG, repo_name),
            {"sha": new_commit["sha"]})
    else:
        api("POST", "/repos/%s/%s/git/refs" % (ORG, repo_name),
            {"ref": "refs/heads/main", "sha": new_commit["sha"]})

    return new_commit["sha"]


def parse_repo_spec(spec):
    """Parse 'repo' or 'repo:subdir' into (repo_name, subdir)."""
    if ":" in spec:
        repo_name, subdir = spec.split(":", 1)
        return repo_name, subdir
    return spec, None


def sync_folder(rel_path, dry_run=False):
    """Ensure one workspace folder is fully in git. Returns (action, detail)."""
    abs_path = os.path.join(WORKSPACE, rel_path)
    if not os.path.isdir(abs_path):
        return ("skip", "not a directory")

    spec = FOLDER_MAP.get(rel_path)
    if not spec:
        # Goals' cron definitions -> tracker repo's crons/ directory.
        if rel_path.startswith("goals/") and rel_path.endswith("/crons"):
            repo_name, subdir = "cross-thread-task-status-tracker", "crons"
        else:
            # Auto-name: workspace-<basename>
            basename = os.path.basename(rel_path.rstrip("/")).replace("_", "-")
            repo_name, subdir = "workspace-%s" % basename, None
    else:
        repo_name, subdir = parse_repo_spec(spec)

    work_files = find_work_files(abs_path)
    if not work_files:
        return ("skip", "no work product")

    git_dir = os.path.join(abs_path, ".git")
    if os.path.isdir(git_dir):
        # It's a clone: find uncommitted changes.
        _, out, _ = run_git(abs_path, "status", "--porcelain")
        changed = [ln for ln in out.splitlines()
                   if "__pycache__" not in ln]
        if not changed:
            return ("ok", "already in git")
        # Collect changed file paths.
        to_commit = []
        for ln in changed:
            fp = ln[3:].split(" -> ")[-1].strip().strip('"')
            full = os.path.join(abs_path, fp)
            if os.path.isfile(full) and is_work_product(full):
                to_commit.append((fp, full))
        if not to_commit:
            return ("ok", "only non-work-product changes")
        if dry_run:
            return ("would-commit", "%d files" % len(to_commit))
        sha = commit_files_to_repo(
            repo_name, to_commit,
            "backup: sync %d uncommitted files from %s" % (len(to_commit), rel_path))
        return ("committed", "%d files -> %s" % (len(to_commit), sha[:8]))
    else:
        # Not a git repo.
        # If mapped to an existing repo (via FOLDER_MAP or goals/crons rule),
        # stage files into the local clone under the target subdir.
        # If not mapped, create a new GitHub repo.
        is_mapped = (rel_path in FOLDER_MAP or
                     (rel_path.startswith("goals/") and rel_path.endswith("/crons")))
        if is_mapped:
            # Find the local clone for this repo.
            clone_path = None
            for k, v in FOLDER_MAP.items():
                v_repo, _ = parse_repo_spec(v)
                if v_repo == repo_name and k.startswith("repos/"):
                    clone_path = os.path.join(WORKSPACE, k)
                    break
            if clone_path and os.path.isdir(os.path.join(clone_path, ".git")):
                # Copy files into clone under subdir (from spec, or folder
                # basename if not specified).
                dest_subdir = subdir or os.path.basename(rel_path.rstrip("/"))
                dest_base = os.path.join(clone_path, dest_subdir)
                to_commit = []
                for fp in work_files:
                    rel_fp = os.path.relpath(fp, abs_path)
                    dest = os.path.join(dest_base, rel_fp)
                    if dry_run:
                        to_commit.append((os.path.join(dest_subdir, rel_fp), fp))
                    else:
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with open(fp, "rb") as src, open(dest, "wb") as dst:
                            dst.write(src.read())
                        to_commit.append((os.path.join(dest_subdir, rel_fp), dest))
                if dry_run:
                    return ("would-commit",
                            "%d files to %s/%s/" % (len(to_commit), repo_name, dest_subdir))
                sha = commit_files_to_repo(
                    repo_name, to_commit,
                    "backup: import %s (%d files)" % (rel_path, len(to_commit)))
                return ("committed",
                        "%d files -> %s/%s/ (%s)" % (len(to_commit), repo_name, dest_subdir, sha[:8]))
        # Not mapped or no clone: create new repo.
        if dry_run:
            return ("would-create", "%s with %d files"
                    % (repo_name, len(work_files)))
        created = ensure_github_repo(repo_name)
        to_commit = [(os.path.relpath(fp, abs_path), fp) for fp in work_files]
        sha = commit_files_to_repo(
            repo_name, to_commit,
            "backup: initial commit of %s (%d files)" % (rel_path, len(to_commit)))
        action = "created+committed" if created else "committed"
        return (action, "%d files -> %s (%s)" % (len(to_commit), sha[:8], repo_name))


def main(argv):
    dry_run = "--dry-run" in argv
    as_json = "--json" in argv

    # EXPLICIT ONLY: scan FOLDER_MAP entries. No auto-discovery — that
    # catches venvs, caches, and runtime dirs. New folders are added to
    # FOLDER_MAP deliberately, not by accident.
    to_scan = list(FOLDER_MAP.keys())

    # Goals' cron definitions: <workspace>/goals/<goal>/crons/ -> tracker crons/
    goals_dir = os.path.join(WORKSPACE, "goals")
    if os.path.isdir(goals_dir):
        for goal in sorted(os.listdir(goals_dir)):
            crons_dir = os.path.join(goals_dir, goal, "crons")
            if os.path.isdir(crons_dir):
                rel = os.path.join("goals", goal, "crons")
                # Map dynamically (not in FOLDER_MAP).
                to_scan.append(rel)

    # Loose .py files in workspace root go to workspace-root-scripts.
    root_py = [f for f in os.listdir(WORKSPACE)
               if f.endswith(".py") and os.path.isfile(os.path.join(WORKSPACE, f))]
    if root_py:
        to_scan.append(".")  # Special: workspace root itself.

    results = {}
    for rel in sorted(set(to_scan)):
        if rel == ".":
            # Handle loose root files specially.
            abs_path = WORKSPACE
            repo_name = "workspace-root-scripts"
            work_files = [os.path.join(WORKSPACE, f) for f in root_py]
            if dry_run:
                results[rel] = ("would-create",
                                "%s with %d files" % (repo_name, len(work_files)))
            else:
                ensure_github_repo(repo_name)
                to_commit = [(f, os.path.join(WORKSPACE, f)) for f in root_py]
                sha = commit_files_to_repo(
                    repo_name, to_commit,
                    "backup: workspace root scripts (%d files)" % len(to_commit))
                results[rel] = ("committed",
                                "%d files -> %s" % (len(to_commit), sha[:8]))
            continue
        action, detail = sync_folder(rel, dry_run=dry_run)
        results[rel] = (action, detail)

    if as_json:
        print(json.dumps({k: {"action": a, "detail": d}
                          for k, (a, d) in results.items()}, indent=2))
    else:
        for rel, (action, detail) in sorted(results.items()):
            print("%-40s %-18s %s" % (rel, action, detail))

    # Exit 1 if anything was committed/created (needs attention).
    needs_attention = any(a in ("committed", "created+committed", "would-commit",
                                "would-create")
                          for a, _ in results.values())
    return 1 if needs_attention else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
