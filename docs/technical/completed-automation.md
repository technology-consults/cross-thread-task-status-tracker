# Completed automation

**Created:** 2026-09-28 · **Last modified:** 2026-10-03

## Plain words

After you approve a piece of work, a chain of follow-up steps has to happen:
the work task moves forward, code gets committed, tagged and deployed, the
live site gets checked, and the task finally closes. Until now those steps
were done by hand in the chat. `scripts/completed.py` does them automatically
— but only on your written approval, only through mechanisms that have
already proven they work, and only when the project's tests pass. Anything
it cannot do safely, it leaves alone and reports.

## What it does

**Phase 1 — apply your verdict.** It finds work tasks waiting on a review
(`blocked_completed`) and reads the review task's verdict line
(`Verdict: approved` / `Verdict: rejected`, which is your written approval).
Approved → the work task moves to `completed`. Rejected → it moves to
`not_approved` for rework. A review with no verdict line is never guessed at —
it is reported for a human.

**Phase 2 — post-actions.** For each `completed` task it runs the post plan
written on the task (see "The post plan" below):

- `none` — nothing to deploy → straight to `done`.
- `message` — posts the given text to the tracker thread → `done`.
- `artifact` — checks the file exists → `done`.
- `code` — the full chain: tests must pass → commit+push → release tag →
  deploy → check the live site → `done`. Every step is recorded on the task
  (commit link, tag, what the live check found).

**What it never does.** It never moves a task without your verdict. It never
deploys through a mechanism that hasn't been proven on a real call. It never
deploys when the tests fail or when no test suite exists. It never runs twice
on the same task (each finished task carries its completion record). If a
deploy breaks, the task stays in `completed` and the failure is reported —
fix forward, never silent rollback. The hourly watcher's `completed_stalled`
sweep is the safety net for anything that stalls here.

## The post plan

When work is submitted for your review, the work task carries a `post`
object describing what happens after you approve. Example:

```json
"post": {
  "kind": "code",
  "repo": "technology-consults/trading-portal",
  "files": ["etf-live.html"],
  "profile": "trading-portal-pages",
  "tag": "v1.1.0",
  "verify": {"url": "https://technology-consults.github.io/trading-portal/etf-live.html",
             "match": "/*__BUNDLE_START__*/"}
}
```

- `kind`: `none` | `message` | `artifact` | `code`.
- `repo` / `files`: what gets committed (repo-first: committed before deploy).
- `profile`: a named, verified deploy mechanism from
  `scripts/deploy_profiles.json`.
- `tag`: the release tag (your pick or semver convention) — put on the
  deployed commit before deploy.
- `verify`: the live check — a URL and a text fragment that must appear in
  it (content check, never "the file changed").

No post plan → the task waits in `completed` and is reported for manual
handling. Plans are never guessed.

## Deploy profiles

`scripts/deploy_profiles.json` holds one entry per deploy target. A profile
exists only after its mechanism proved out on a real call:

| Profile | Target | Mechanism (proven) | Gate |
|---|---|---|---|
| `board-push` | board files | Root `push_board.py --publish`: GitHub API commit of board files + KV PUT to the portal namespace (`p:board`, `p:tasks.json`, `p:assets/board.css`). The board page loads `tasks.json` live from the repo's main branch on every page view (KV snapshot is the fallback). At publish, the `__BUILD_SHA__` placeholder in `index.html` is stamped with the short SHA of the deployed main HEAD, shown top-right as the build version. | `tests/regression.py` (run manually before every publish) |
| `github-repo-push-tag` | script repos (trading, short-video, vehicle) | GitHub API commit + release tag | changed `.py` files must compile |
| `trading-portal-pages` | trading-portal site | API push → Pages auto-deploy → live URL check | **missing** — stays manual until a suite exists |
| `portal-kv-content` | portal content pages | project's KV push scripts → live URL check | **missing** — stays manual until a suite exists |

Deliberately absent: bandhu-portal **worker** code — no proven deploy path
exists, so those tasks stay manual until one is proven and tested.

Adding a new profile: prove the mechanism with a real call first, write the
regression suite, add the profile with the proof noted, and extend
`tests/regression.py`. No proof, no profile.

## Running it

Dry-run (default, changes nothing):

```
python3 scripts/completed.py
```

Actually move tasks and deploy:

```
python3 scripts/completed.py --execute
```

Test against a fixture instead of the live board:

```
python3 scripts/completed.py --tasks /tmp/fixture-tasks.json
```

After it changes any statuses, publish the board so the updates go out.
The board page (`p:board`) renders from `p:tasks.json`, so publishing is:
(1) run `python3 tests/regression.py` — must be 12/12 before anything ships;
(2) commit `tasks.json` to the repo via the GitHub API; (3) PUT the same
bytes to the portal KV namespace as key `p:tasks.json`; (4) fetch the live
`https://portal.technology-consults.workers.dev/p/tasks.json` and confirm the
change is there. The old `scripts/push_board.py --publish` path is retired —
it reads from `board-build/`, which was archived on 2026-09-28.

The scheduled runner (a cron, created after this automation is approved)
runs `completed.py --execute` then `push_board.py --publish` when anything
changed, and delivers the printed `COMPLETED-ACTION` / `MANUAL` blocks to the
project tracker threads. Until that cron exists, the interim manual thread
moves stay in effect.

## Testing

`tests/regression.py` covers the automation: `--help` exits clean, dry-run
against a fixture applies an approval verdict and runs a full code
post-action plan without touching the live board, and every deploy profile is
valid JSON with a proven mechanism note. Exit non-zero = do not ship.
