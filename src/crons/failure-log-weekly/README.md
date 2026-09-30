# failure-log-weekly

*Job package for the versioned-cron architecture. Created: 2026-09-30 · Last modified: 2026-09-30*

Weekly (Monday 08:00 America/Toronto) digest of `verifier/failures.md` in
this repo, delivered to the failure log side chat
(`de5d7ab8-9709-4e7c-a556-fd5f582b2f7e`).

## Layout

| File | What it is |
|---|---|
| `run.py` | Package entrypoint: fetch → parse → 7-day filter → report |
| `github_api.py` | Minimal contents-API helper (vendored per job; api.github.com only) |
| `tests/test_failure_log.py` | Unit tests (fetch stubbed) |

## Track B: script-as-orchestrator

**No agent step.** Fetching the file, parsing numbered entries under
`## Entries (newest last)`, filtering the window (today − 6 days … today),
and composing the report are all deterministic, so the script does all of
it and the exit-10 handshake never fires.

## Reply contract

- File missing: graceful note, exit 0, no chat delivery.
- Entries in window: the report (newest first), printed for chat delivery.
- No entries in window: explicit no-new-failures report.
- Unparseable numbered lines under the Entries heading are skipped with a
  count note in the output.
