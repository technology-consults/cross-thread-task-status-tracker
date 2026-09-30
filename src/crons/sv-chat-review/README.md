# sv-chat-review

*Job package for the versioned-cron architecture. Created: 2026-09-30 · Last modified: 2026-09-30*

Twice daily (~06:00 and ~12:00 America/Toronto) review of the SV tracker
thread (`d82796e3-56f1-4d34-bf51-665165a38e92`): extract proposals,
decisions, agreements, gates and tasks, then file them. Runs the 06:00–12:00
and 12:00–24:00 windows.

## Layout

| File | What it is |
|---|---|
| `run.py` | Package entrypoint: watermarks → extract handshake → file handshake → digest |
| `tests/test_chat_review.py` | Unit + handshake tests |

## Track B: script-as-orchestrator, two agent rounds

- **Script-driven:** watermark storage (seeded once from the short-video
  goal's hidden_files `chat_review_state.json`), result validation, and the
  final digest.
- **Agent-driven (handshake):** round 1 extracts items from the thread since
  the watermark (reading chat history is agent work); round 2 files them —
  GitHub API doc updates, board `[DECISION]`/`[BUILD]`/`[REVIEW]` tasks,
  `program.json` records, gate summaries to the SV tracker + For review
  thread (`b95fb15f-a58f-4547-b9cd-cdce882a5cd9`), reversible autonomous
  implementation — applying the autonomy rules carried in the filing task
  (never credentials/auth work, never other owners' repos, ambiguous text
  → research + best interpretation recorded).

Handshake: script exits 10 with `@@AGENT-REQUEST-BEGIN@@` JSON
`{need, task, schema, attempt}` per round; results schema-validated; max 5
rounds per request, then exit 20 (fail loudly, never partial).

## Runtime data (not code)

- `CRON_JOB_STATE_DIR` env, else
  `<home>/.cron_runner/job_state/sv-chat-review/` — `watermarks.json`
  (`sv` = newest message id seen).
- First run seeds from
  `<home>/workspace/goals/short-video-creation-and-publishing-pipeline/hidden_files/chat_review_state.json`
  if it exists; otherwise the first review starts with today's messages.

## Reply contract

- Nothing new: `SV chat review: nothing new since <watermark>.`
- Filed: a digest — counts by action, where each item landed, errors listed.
