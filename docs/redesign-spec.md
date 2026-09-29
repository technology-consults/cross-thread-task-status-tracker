# Board redesign — specification (2026-09-28)

BalRam's written decisions. No code until he gives written OK on this spec.

## 1. Status model (14 statuses)

| Status | Meaning | Owner while here |
|---|---|---|
| `todo` | Newly created, awaiting approval/start | whoever will do it |
| `approved` | Green-lit, ready to be worked | worker |
| `in_progress` | Work has actually started | worker |
| `pending_review` | BalRam's review task | BalRam |
| `pending_review_post_discussion` | BalRam asked for clarification during review | Bandhu |
| `not_approved` | BalRam rejected the work; rework needed | Bandhu |
| `blocked` | Cannot continue — dependency | whoever was working |
| `blocked_discuss` | Blocked and needs discussion | Bandhu |
| `blocked_completed` | Work finished, waiting on BalRam's review task | (waiting) |
| `blocked_approved` | Blocked before approval; becomes `approved` when clear | worker |
| `parked` | Deferred | — |
| `completed` | Review passed; post-actions (push/tag/deploy/verify or artifacts/messages/verify) running | automation |
| `done` | Everything finished and verified | — |
| `rejected` | Permanently rejected | — |

Terminal: `done`, `rejected`. `completed` is NOT terminal — it is the automation trigger.
There is NO generic `blocked_X` family. Only the statuses above exist.

## 2. Allowed transitions (the map)

| From | To | Trigger |
|---|---|---|
| `todo` | `approved` | BalRam green-lights (chat agreement counts) |
| `todo` | `in_progress` | Bandhu starts agreed work |
| `todo` | `parked` / `rejected` | Defer / permanently reject |
| `approved` | `in_progress` | Work starts |
| `approved` | `parked` / `rejected` | Defer / reject |
| `approved` | `blocked` | Dependency discovered before start |
| `in_progress` | `blocked_completed` | Bandhu finishes → BalRam's `pending_review` task is created, work task blocked by it |
| `in_progress` | `blocked` | Dependency hit |
| `in_progress` | `parked` | Defer |
| `blocked` | `in_progress` | Blockers cleared, resume |
| `blocked` | `blocked_discuss` | Discuss → paste message → on receipt assign Bandhu |
| `blocked` | `parked` | Defer |
| `blocked_discuss` | `blocked` | Discussion parked, still blocked |
| `blocked_discuss` | `in_progress` | Resolved, resume |
| `blocked_approved` | `approved` | Blockers cleared (watcher) |
| `blocked_completed` | `completed` | BalRam approves on the review task (pasted message) |
| `blocked_completed` | `not_approved` | BalRam rejects on the review task |
| `not_approved` | `in_progress` | Rework starts |
| `not_approved` | `parked` / `rejected` | Defer / give up |
| `pending_review` | `done` | BalRam decides; verdict text `approved` or `rejected` written on the task |
| `pending_review` | `pending_review_post_discussion` | BalRam asks for clarification → assign Bandhu |
| `pending_review_post_discussion` | `pending_review` | Clarification supplied → assign BalRam |
| `parked` | `todo` | Unparked |
| `parked` | `rejected` | Permanently rejected |
| `completed` | `done` | Post-actions succeeded and verified; commit link recorded on the work task |
| `completed` | `in_progress` | Post-action failed → fix and re-run (watcher reports the stall) |
| `done` / `rejected` | — | Terminal, no outgoing transitions |

### Button → transition wiring

- Approve on `pending_review` → review task `done` (verdict `approved`); waiting task's block on the review task removed; waiting task → `completed`.
- Reject on `pending_review` → review task `done` (verdict `rejected`); waiting task's block removed; waiting task → `not_approved`.
- Rework finished (`not_approved` → `blocked_completed`) → a NEW `pending_review` task is created with a cumulative summary of all earlier + latest changes.
- Clarification request on `pending_review` → paste message → on receipt: assign Bandhu, task → `pending_review_post_discussion`.
- Discuss on `blocked` → paste message → on receipt: assign Bandhu, task → `blocked_discuss`.
- Every portal button generates a paste-message for BalRam; the portal cannot write board data.

### Per-status board buttons (only valid next transitions shown)

| Status | Buttons |
|---|---|
| `todo` | Approve · Start work · Park · Reject |
| `approved` | Start work · Park · Reject · Block |
| `in_progress` | Mark finished · Block · Park |
| `blocked` | Discuss · Mark cleared · Park |
| `blocked_discuss` | Back to blocked · Resume work · Park |
| `blocked_completed` | none (waits on review task) |
| `blocked_approved` | none (watcher moves it when clear) |
| `pending_review` | Approve · Reject · Ask for clarification |
| `pending_review_post_discussion` | Send clarification (→ `pending_review`) |
| `not_approved` | Start rework · Park · Reject |
| `parked` | Unpark (→ `todo`) · Reject |
| `completed` | none (automation owns it; watcher is the safety net) |
| `done` / `rejected` | none (terminal) |

## 3. Migration of existing tasks

| Old | New | Note |
|---|---|---|
| `agreed` | `done` | 47 tasks (his 2026-09-28 call: old "agreed" = completed) |
| `blocked_agreed` | `blocked_approved` | if any exist |
| `code_completed` | `blocked_completed` | if any exist |
| `pending_me` | dropped | no tasks currently use it; `assigned_to` takes over |
| `in_progress` + `(yours)` in title | `pending_review`, assigned BalRam | existing review tasks |
| `in_progress` (others) | `in_progress`, assigned Bandhu | |
| `blocked` | `blocked` | assigned per rule below |
| `parked` | `parked` | assigned per rule below |
| `rejected` | `rejected` | |
| `done` | `done` | already terminal under the new model |

`assigned_to` backfill: title contains `(yours)` → `BalRam`; otherwise → `Bandhu`.
`created` backfill: first appearance in board git history; blank where not provable.
Summary: extracted dynamically from the detail text at render/digest time. No new field.

## 4. New-task rules

- BalRam review task → `pending_review`. Other BalRam tasks → `todo`.
- Bandhu tasks → `todo`; → `in_progress` only when work genuinely starts.

## 5. Board UI

- `assigned_to` shown on each card + a board filter for it.
- Transition buttons per the table in §2; Discuss on blocked/review tasks; Approve on `pending_review`.
- Portal buttons generate the paste message; no direct board writes from the portal.

## 6. Digests (two, after every board update; the watcher sends none)

Digest 1 — needs action: `todo`, `pending_review`, `blocked`, `blocked_discuss`, `pending_review_post_discussion`, `not_approved`.
Digest 2 — everything else reportable: `in_progress`, `parked`, `approved`, `done`, `blocked_completed`, `blocked_approved`.
Neither digest includes `completed` or `rejected`.

Columns: title · summary (dynamic) · status · assigned to · created · due.
Landscape PDF, white text on the accent-colour header. One stable `*-latest.pdf` per digest, rotated — only the latest lives, nothing piles up in Artifacts.

## 7. `completed` automation + safety net

`completed` triggers: code tasks → commit/push, release tag, deploy, verify, tracker messages → `done`; non-code tasks → artifacts, messages, other post-actions, verify → `done`; nothing to do → straight to `done` after confirming.
A watcher detects tasks stuck in `completed` (post-action failed) and reports the failure to the tracker.
Interim (locked 2026-09-28): until this automation is built, the `blocked_completed` → `completed` → post-actions moves happen manually via the thread — nothing moves without his written approval.

## 8. Resolved design decisions (BalRam, 2026-09-28)

1. Review tasks carry a summary of changes only — no commit link. The commit link goes into the work task when it moves `completed` → `done`.
2. Watcher never delivers digests; every board update already triggers them. One latest PDF per digest lives; nothing accumulates.
3. "Completed task" in the rejection flow meant `blocked_completed`. Reject: waiting task `blocked_completed` → `not_approved`, block on the review task removed; review task → `done` with verdict `approved`/`rejected`.
4. SHIP is parked for manual direction only; push/deploy ride on review-task approval.
5. No generic `blocked_X` status family.
6. Board buttons exist only for BalRam's actions. Bandhu's own moves (e.g. pulling a task back to `in_progress` on review feedback) happen via the thread and need no button or transition on the board.
7. Clicking a dependency (or any task-id) link always lands on the task: if the status filter hides the target, the click resets the status filter to All first (and the reset is saved). The thread filter is never touched — no cross-thread dependencies are expected.
8. Old `blocked` tasks whose review was approved before the work was done: when the work finishes and moves to `blocked_completed`, a NEW review task is created (summary of finished work, per the submit-for-review ritual) and added to the work task's `blockedBy`. Approving that review drives `blocked_completed` → `completed` → post-actions → `done`. The old (already-approved) review stays in `blockedBy` as history; it is `done` so it blocks nothing.

## 9. Tests before review

Real production flow (actual board files, actual push path), mobile layout (narrow viewport card grid, wrapping, shortened URLs), paste-message transitions end to end, both digest PDFs regenerating with the stable filenames, watcher modes unchanged.
