---
id: agent-working-files-backup
title: Agent working files backup
enabled: true
mode: task
schedule:
  kind: daily
  timezone: America/Toronto
  time: 02:00:00
timeout_secs: 900
delivery:
  - chat_id: 9c6459ad-00f6-47e3-a7ca-0754d25fc408
metadata:
  originating_chat_context_json: '{"chat_id":"9c6459ad-00f6-47e3-a7ca-0754d25fc408","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
Daily backup of the agent's working files to the private repo `technology-consults/agent-working-files`.

Steps:
1. Resolve `main` to its exact SHA:
   `python3 ~/workspace/skills/github/bin/gh_api.py GET "/repos/technology-consults/agent-working-files/git/refs/heads/main"`
   and read `.object.sha`.
2. Download that SHA's tarball, keeping the credential strictly on api.github.com. Use this pattern (mirrors the established run_from_git.py approach):
   - Build the request to `https://api.github.com/repos/technology-consults/agent-working-files/tarball/<SHA>` and attach the credential via `dynamic_credentials.add_surrogate_to_request(req, "custom.github", allowed_hosts=["api.github.com"])` (prepend `/opt/hatch/skills/skill-creator/bin` to sys.path).
   - Open it with a no-redirect opener (an HTTPRedirectHandler whose redirect_request returns None). Expect the 302; take the `Location` header (a signed codeload URL).
   - Fetch that signed URL with a PLAIN unauthenticated request (the signature is the auth) — the credential must never leave api.github.com.
   - Extract into a brand-new directory `/tmp/awf-backup-<UTC timestamp>`. Never reuse a previous directory, never use git or a git clone. The repo root is the single inner directory created by the extraction (the one containing `scripts/`).
3. Run from the repo root: `python3 scripts/backup_working_files.py`
4. Reporting: if the script outputs exactly `no changes`, end with that one line and nothing more — stay silent. If it outputs `backup: committed <sha> (...)`, report briefly: which files changed and the commit SHA. If any step fails, report the failure briefly: which step failed and the error text.

Rules: GitHub API only — never `git push`, never the browser. Never print file contents or secrets — only file names and commit SHAs.
