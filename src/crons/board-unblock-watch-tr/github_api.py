#!/usr/bin/env python3
"""Minimal GitHub contents-API helper for versioned cron jobs.

GET/PUT files via api.github.com only (never raw.githubusercontent.com,
never the browser). Auth: Muse-runtime credential surrogate
(custom.github), same pattern as the repo's own scripts.

Vendored per job package (self-contained; no cross-job imports).
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error

sys.path.insert(0, "/opt/hatch/skills/skill-creator/bin")
try:
    from dynamic_credentials import add_surrogate_to_request
except ImportError:  # pragma: no cover - surrogate absent in some test envs
    add_surrogate_to_request = None

API = "https://api.github.com"


class GitHubError(RuntimeError):
    def __init__(self, method, path, code, body):
        super().__init__("GitHub %s %s: HTTP %s %s"
                         % (method, path, code, body[:200]))
        self.code = code


def _req(method, path, payload=None):
    if add_surrogate_to_request is None:
        raise RuntimeError("GitHub credential surrogate unavailable; "
                           "cannot call the API")
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"User-Agent": "muse-cron-job",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    add_surrogate_to_request(req, "custom.github",
                             allowed_hosts=["api.github.com"])
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
            return json.loads(raw.decode()) if raw else {}
    except urllib.error.HTTPError as e:
        raise GitHubError(method, path, e.code, e.read().decode())


def get_contents(repo, path, ref="main"):
    """Return (text, sha) for repo/path@ref. Raises GitHubError."""
    r = _req("GET", "/repos/%s/contents/%s?ref=%s" % (repo, path, ref))
    return base64.b64decode(r["content"]).decode("utf-8"), r["sha"]


def put_contents(repo, path, text, sha, message, branch="main"):
    """PUT text to repo/path@branch. Returns the commit sha."""
    payload = {"message": message,
               "content": base64.b64encode(text.encode("utf-8")).decode(),
               "branch": branch,
               "sha": sha}
    r = _req("PUT", "/repos/%s/contents/%s" % (repo, path), payload)
    return r["commit"]["sha"]
