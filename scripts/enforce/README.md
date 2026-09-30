# scripts/enforce/ — plain-words guide

Created: 2026-09-30. Last modified: 2026-09-30.

## What this is

A set of automatic checks that run **before every commit** to this repo.
They are the owner's standing rules, written as code — not as text in a
chat — so they apply the same way every time, no matter which agent is
committing.

`scripts/commit.py` is the only way to commit here. It runs, in order:

1. **Unit tier** — `tests/run_unit.py` must be fully green.
2. **These checks** — over the lines your commit adds or changes.
3. **The commit itself** — one atomic GitHub API commit for all files.

If any check fails, nothing is committed, and you get a printed
procedure telling you exactly what to do next (fix your code, propose a
rule change, or request an exception — there is no silent bypass).

## The checks, in plain words

**Code quality** (`coding_standards.py`)
- Every Python file must be valid Python (it must compile).
- No dangerous shortcuts: no `eval`/`exec`, no shell commands from code,
  no unpickling data, no unsafe YAML loading.
- No bare `except:` — always name the error you are catching.
- No cache junk (`__pycache__`, `.pyc`, `.DS_Store`) in git.
- If you add a new function or class in `scripts/`, `src/`, or
  `crons/shared/`, the same commit must add or update a test for it.

**Security** (`security.py`)
- No secrets in committed code: no API keys, tokens, or passwords with
  real values, no private-key files. (Tests use fake values built at
  runtime, never typed out.)
- Never print or log a credential value.

**Owner's rules** (`owner_guidelines.py`)
- No platform command-line tools (Instagram, Facebook, Threads,
  YouTube, TikTok, X) — always use the platform's own API instead.
- New documentation pages go under `docs/technical/`, not loose in
  `docs/`.
- The repo keeps a single combined documentation PDF, never one PDF
  per page.
- If your code needs something that only exists inside the Muse agent
  runtime, the same commit must add a row to
  `docs/technical/portability-notes.md` saying what and why.
- GitHub is API-only: scripts must never push through the git command;
  every write goes through `api.github.com`.
- Never fetch repo files from the raw-file CDN host — it triggers a
  phone approval prompt. All GitHub reads go through `api.github.com`
  (the contents API for files, the tarball endpoint for archives).
  A separate whole-tree scanner (`no_raw_githubusercontent.py`) audits
  already-committed files; this gate checks new diffs.

**Board integrity** (`board_integrity.py`)
- `tasks.json` is the board itself, written by several agents at once.
  Whenever a commit touches it, the whole file is validated: it must be
  valid JSON, every task must have its required fields (`id`, `thread`,
  `title`, `status`, `updated`, `detail`), ids must be unique text,
  every status must be one the board page understands, and every task's
  thread must exist on the board. One bad write can break every reader,
  so a bad file never lands.

**What happens when a check blocks you** (`remediation.py`)
- The commit stops and prints the procedure. Three legitimate ways
  forward: fix your code (no approval needed), propose a rule change
  through discussion and agreement, or request a one-time exception.
  Enforced rules are locked — nobody changes them alone.

## The deliberate-act escape: allowlists

Each check has an `allowlist_*.txt` file. Adding a path there is a
deliberate, reviewed act that exempts exactly that path — the escape
hatch for the rare legitimate exception. All of them start empty, and a
missing allowlist file exempts nothing (fail closed).

## Versioning

`gates.json` is the machine-readable inventory of every check, with a
`ruleset_version`. The whole `scripts/enforce/` directory is hashed, and
`tests/test_ruleset_version.py` pins that hash: the version everyone
agreed is exactly the version that enforces every commit. Changing a
rule means bumping the version and re-pinning the hash in the same
commit — after discussion and agreement, never alone.

## Adapting vs the short-video reference

This suite is modeled on short-video's `scripts/enforce/`, with these
deliberate differences:
- **New module** `board_integrity.py`: short-video has no shared
  concurrently-written JSON file; this repo's board does, so it gets
  its own schema gate.
- **Code dirs** for the tests-with-code check are `scripts/`, `src/`,
  and `crons/shared/` (this repo's code homes) instead of short-video's
  `build/`, `program/`.
- **Dropped** short-video's no-video gate (this repo is not a video
  pipeline).
- **Kept** this repo's existing whole-tree raw-CDN scanner
  (`no_raw_githubusercontent.py`, committed earlier) untouched; the new
  diff-based `no-raw-github` gate complements it.
- **Remediation** speaks about board-critical work (the board unreadable
  or unwritable) instead of video publishing, and exception tasks must
  name a real board thread (`sv`, `tr`, `vh`).
- **Unit tier** is `tests/run_unit.py` (fast, no network), not a tiered
  pipeline runner — this repo's heavier suites hit live sites or
  scheduler state and stay out of the pre-commit path.
