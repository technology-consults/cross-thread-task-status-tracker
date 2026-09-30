# Workspace Directory Guide

**Created:** 2026-09-28 11:53 EDT · **Last modified:** 2026-09-29 09:05 EDT

A plain-words map of everything in the workspace: what each directory is for, and what each file underneath it does. Machine-generated bulk (caches, logs, snapshots) is grouped by pattern with counts instead of one row per file — those rows would add noise, not information.

**Note (2026-09-28):** the workspace was reorganized around 11:52 EDT, minutes before this guide was built — project sources moved into local git clones under `repos/`, and the old folders were archived under `archive/` with a `-2026-09-28` date stamp. `board-build/`, `etf-alerts/`, `portal/`, and `short-video-docs-html/` no longer exist at the top level.

## At a glance

| Directory | What it's for | Files |
|---|---|---|
| `agents/` | Saved records of past agent tool calls (debugging cache) | ~237, grouped |
| `archive/` | Retired source folders, date-stamped snapshots (read-only history) | 5 folders, ~248 files |
| `artifact-index-build/` | Staging copies used to build the Artifact Index page | ~51 |
| `cron.d/` | Definitions for every recurring background job (7 live + retired archive) | 7 live |
| `etf-charts/` | One leftover ETF chart sample | 1 |
| `feature-request/` | Feedback/failure reports filed to the Muse product team | 4 |
| `feed/` | Working data for your personal Feed (newspaper) | ~202, grouped |
| `github-test/` | Leftover from the 2026-09-27 GitHub API test | 1 |
| `goals/` | One workspace per durable goal: notes, schedules, run logs, deliverables | ~199 |
| `imagine_media/` | AI-generated video clips + thumbnails + metadata | 9 |
| `memory/` | Machine-generated memory-reconciliation records | ~34, grouped |
| `objectives/` | The agent's own background-study notes | 2 |
| `onboarding_tour/` | Screenshots for the product's onboarding tour | 4 |
| `private/` | Chat-private context folders (never leave their chat) | 3 |
| `repos/` | Local git clones of the six project repos — the live sources of truth | ~142 |
| `scheduler/` | Empty placeholder | 0 |
| `self_improvement/` | The agent's background self-improvement loop (state + staging) | ~458, grouped |
| `shared/` | Shared context library (global + per-category layers, templates, holidays) | 8 |
| `short-video/` | Short-video working files: intro-video assets, doc-build scratch, publish notes | ~36 |
| `skills/` | Reusable playbooks: one guide + helper scripts per service | ~38 |
| `space_data/` | Auto-generated preview/thumbnail images for web spaces | ~32, grouped |
| `spaces/` | Empty placeholder | 0 |
| `ts-spaces/` | Legacy web-app build area (five spaces + build outputs) | ~309, grouped |
| `user/` | Files you handed over (uploads) + cached screenshots | ~50 |
| `verifier/` | The independent QC gate: procedure + failure log | 2 |
| `voice_notes/` | Voice-note audio | 1 |
| `your_files/` | User-facing deliverables (what you see in the Artifacts tab) | ~108 |
| `.hatch-browser/` | Browser session snapshots (machine cache) | 1,969, not itemized |
| `.docbuild-venv/` | Python virtual environment for document building (machine cache) | 1,765, not itemized |
| `.jarvis/` | Scratch state from an idea execution | 1 |
| *(root files)* | Loose files at the workspace root | 2 |

---

## `agents/`
Saved records of past agent tool calls — one file per call, filed under the agent's ID. Entirely machine-generated; only useful for debugging what an agent did, never for daily work.

| File | What it is |
|---|---|
| `agents/<id>/tool-output/browser-search-finance-call_*.json` (202 files) | Saved results of past finance web searches (mostly ETF price-history lookups) |
| `agents/<id>/tool-output/context_fetch-call_*.txt` (15 files) | Saved outputs of past context-fetch calls |
| `agents/<id>/tool-output/exec-call_*.json` (9 files) | Saved outputs of past shell-command runs |
| `agents/<id>/tool-output/memory_get-call_*.txt` (5 files) | Saved outputs of past memory reads |
| `agents/<id>/tool-output/browser.list_tasks-call_*.json` (2 files) | Saved outputs of past browser-task listings |
| `agents/<id>/tool-output/tool-call_*.json` (2 files) | Saved outputs of miscellaneous tool calls |
| `agents/<id>/tool-output/subagent.list-call_*.json` (1 file) | Saved output of a past subagent listing |
| `agents/<id>/tool-output/chat.read_messages-call_*.json` (1 file) | Saved output of a past chat-history read |

## `archive/`
Retired source folders, snapshotted with a date stamp after their code moved into the local git clones under `repos/`. Read-only history — the live copies are in `repos/`.

| File | What it is |
|---|---|
| `archive/board-build-2026-09-28/` (9 files) | Archived copy of the status-board page source (index.html, board.css, tasks.json, push_board.py, unblock_watch.py) |
| `archive/etf-alerts-2026-09-28/` (142 files) | Archived copy of the ETF alert/signal builder scripts + the full strategy-backtest research tree |
| `archive/portal-2026-09-28/` (22 files) | Archived copy of the portal source (Cloudflare worker, pages, tests, deploy scripts) |
| `archive/short-video-docs-html-2026-09-28/` (45 files) | Archived copy of the short-video documentation HTML site |
| `archive/short-video-repo-2026-09-28/` (30 files) | Archived copy of the short-video publishing-pipeline architecture docs |

## `artifact-index-build/`
Staging copies of user-facing artifacts (documents, the docs site, the ETF live page) used to build the Artifact Index page that gets pushed into the cross-thread GitHub repo.

| File | What it is |
|---|---|
| `artifact-index-build/artifacts/index.html` | The Artifact Index page itself (list of artifacts with links) |
| `artifact-index-build/muse-artifacts/Short-Video-Business-Model-Risk-Register.docx` | Index copy of the risk-register document |
| `artifact-index-build/muse-artifacts/Short-Video-Comprehensive-Business-Plan.docx` | Index copy of the business-plan document |
| `artifact-index-build/muse-artifacts/etf-live-bundle.json` | Index copy of the ETF live-app data bundle |
| `artifact-index-build/muse-artifacts/etf-live.html` | Index copy of the ETF live web app page |
| `artifact-index-build/muse-artifacts/short-video-project-full.zip` | Index copy of the full short-video project zip |
| `artifact-index-build/muse-artifacts/short-video-docs/00-START-HERE.html` | Docs-site landing page copy |
| `artifact-index-build/muse-artifacts/short-video-docs/index.html` | Docs-site home copy |
| `artifact-index-build/muse-artifacts/short-video-docs/brand/voice-*.mp3` (4 files) | Narrator voice samples (radiant, sleek, smooth, warm) |
| `artifact-index-build/muse-artifacts/short-video-docs/create-and-publish/plan.html` | Create-and-publish pipeline plan |
| `artifact-index-build/muse-artifacts/short-video-docs/create-and-publish/tasks-balram.html` | Your task list for that pipeline |
| `artifact-index-build/muse-artifacts/short-video-docs/create-and-publish/tasks-muse.html` | The agent's task list for that pipeline |
| `artifact-index-build/muse-artifacts/short-video-docs/create-and-publish/techspec.html` | That pipeline's technical spec |
| `artifact-index-build/muse-artifacts/short-video-docs/earnings-improvement/` (4 files: plan, tasks-balram, tasks-muse, techspec) | Earnings-improvement pipeline docs |
| `artifact-index-build/muse-artifacts/short-video-docs/housekeeping/` (4 files) | Housekeeping pipeline docs |
| `artifact-index-build/muse-artifacts/short-video-docs/performance-monitoring/` (4 files) | Performance-monitoring pipeline docs |
| `artifact-index-build/muse-artifacts/short-video-docs/promotion/` (4 files) | Promotion pipeline docs |
| `artifact-index-build/muse-artifacts/short-video-docs/ledgers/content-ledger.html` | Content ledger copy |
| `artifact-index-build/muse-artifacts/short-video-docs/ledgers/sponsor-obligations.html` | Sponsor-obligations ledger copy |
| `artifact-index-build/muse-artifacts/short-video-docs/reference/` (7 files) | Reference copies: architecture, brand-kit, content-guardrails, decisions-log, monetization-research, platform-policies, topic-engine-scope |
| `artifact-index-build/muse-artifacts/short-video-docs/research/ai-video-niche-research-20260924-2137/` (5 files) | Niche-research report + notes copies |
| `artifact-index-build/muse-artifacts/short-video-docs/research/creator-sponsorship-affiliate-economics-20260924-2228/` (5 files) | Sponsorship/affiliate research report + notes copies |

## `cron.d/`
The schedule definitions for every recurring background job (one markdown file per job, named by schedule). `_archive/` holds retired definitions.

| File | What it is |
|---|---|
| `cron.d/hourly/board-unblock-watch-sv__interval@1h.md` | Hourly unblock check for the Short Video board |
| `cron.d/hourly/board-unblock-watch-tr__interval@1h.md` | Hourly unblock check for the Trading board |
| `cron.d/hourly/board-unblock-watch-vh__interval@1h.md` | Hourly unblock check for the Vehicle board |
| `cron.d/daily/portal-links-watch__daily@07:42:00_user_current.md` | Daily portal-URL live re-verification |
| `cron.d/daily/regression-watchdog__daily@07:42:00_user_current.md` | Daily regression watchdog |
| `cron.d/minutely/heartbeat__interval@30m.md` | 30-minute heartbeat check |
| `cron.d/weekly/failure-log-weekly__weekly@Sat-09:42:00.md` | Weekly failure-log review, Saturdays |
| `cron.d/_archive/agentic-feature-tour__daily@09:46:00.md` | Retired feature-tour schedule |
| `cron.d/_archive/backtest-report-delivery__runonce@2026-09-26T09:42:00.md` | Retired one-time backtest delivery |
| `cron.d/_archive/board-unblock-watch__interval@12h.md` | Retired 12-hourly board watch |
| `cron.d/_archive/board-unblock-watch__interval@1h.md` | Retired older 1-hourly board watch |
| `cron.d/_archive/etf-price-preclose__daily@15:30:00.md` | Retired older pre-close schedule |
| `cron.d/_archive/etf-price-updates__interval@2h.md` | Retired older price-updates schedule |
| `cron.d/_archive/etf-signal-intraday__interval@2h.md` | Decommissioned intraday watch (replaced by market-hours + off-hours jobs, 2026-09-29) |
| `cron.d/_archive/holiday-list-update__weekly@Sun-20:00:00.md` | Retired weekly holiday schedule (replaced by quarterly, 2026-09-29) |
| `cron.d/_archive/job-watchdog__interval@1h.md` | Retired older watchdog schedule |
| `cron.d/_archive/precon-digest__daily@08:42:00.md` | Retired (disabled) digest schedule |
| `cron.d/_archive/strategy-research-updates__interval@2h.md` | Retired strategy-research schedule (+1 timestamped duplicate) |
| `cron.d/_archive/tiktok-validation-retry__runonce@2026-09-27T14:42:00.md` | Canceled TikTok retry (first attempt) |
| `cron.d/_archive/tiktok-validation-retry__runonce@2026-09-27T14:50:00.md` | Canceled TikTok retry (second attempt) |

## `etf-charts/`
A single leftover chart file from the ETF work, kept as a sample.

| File | What it is |
|---|---|
| `etf-charts/qqq-6m-2026-09-21.html` | Old QQQ 6-month chart widget (2026-09-21) |

## `feature-request/`
Records of feedback/failure reports filed to the Muse product team, plus lock files for the submission flow.

| File | What it is |
|---|---|
| `feature-request/reports.json` | The filed reports (e.g. the credential-handling failure report) |
| `feature-request/.check.lock` | Lock for the check step of the submission flow |
| `feature-request/.operation.lock` | Lock for the operation step of the submission flow |
| `feature-request/.submit.lock` | Lock for the submit step of the submission flow |

## `feed/`
Working data for your personal Feed (your newspaper): cached third-party media, a media index, and dated research notes.

| File | What it is |
|---|---|
| `feed/media/3p/<id>/hero.jpg\|hero.png\|hero.webp` (96 files) | Cached article hero images for feed items, one folder per item |
| `feed/media/index.json` | Index of the cached media |
| `feed/research/<id>/<date-slot>/web.md` (105 files) | Dated feed research notes, one per morning/midday/evening slot |

## `github-test/`
Leftover from the 2026-09-27 GitHub API permission test.

| File | What it is |
|---|---|
| `github-test/tracker-page/index.html` | The test status page created during validation (superseded on the live site by the real board; this local copy remains) |

## `goals/`
One workspace per durable goal. Each goal keeps its own notes (`GOAL.md`), schedules (`crons/`), run logs and state (`hidden_files/`), working notes (`agent_notes/`), references, and user-facing deliverables (`files/`).

### `goals/all-threads-status-board-upkeep/`
Keeps the All Threads Status Board current.

| File | What it is |
|---|---|
| `GOAL.md` | Notes on keeping the status board current |
| `crons/daily/task-due-date-watch__daily@08:42:00_user_current.md` | Daily due-date watch schedule |
| `hidden_files/due_watch.py` | Script that checks task due dates |
| `hidden_files/due_watch_2026-09-28.json` | Latest due-watch run output |

### `goals/builder-email-digest/`
The builder-email digest (currently disabled — stays off until you ask to reactivate).

| File | What it is |
|---|---|
| `GOAL.md` | Notes on the builder digest |
| `crons/daily/precon-digest__daily@08:42:00.md` | Its disabled daily schedule |

### `goals/etf-price-updates/`
The ETF price-alert goal: QQQ/SPY/GLD cards with charts, trading signals, and the live web app.

| File | What it is |
|---|---|
| `GOAL.md` | Notes on the ETF price-alert goal |
| `crons/daily/etf-price-preclose__daily@15:15:00.md` | Pre-close alert schedule |
| `crons/daily/etf-trading-signals__daily@07:30:00.md` | Morning signal-report schedule |
| `crons/daily/signal-scorecard__daily@08:42:00.md` | Signal scorecard schedule |
| `crons/hourly/etf-price-updates__interval@2h.md` | 2-hourly price-alert schedule |
| `crons/hourly/etf-signal-intraday-market__interval@1h.md` | Hourly market-hours signal-watch schedule |
| `crons/hourly/etf-signal-intraday-offhours__interval@6h.md` | 6-hourly off-hours signal-watch schedule |
| `crons/minutely/etf-live-bundle__interval@5m.md` | 5-minute live-bundle rebake schedule |
| `crons/monthly/holiday-list-update__monthly@1-20:00:00.md` | Quarterly NYSE holiday-list refresh schedule |
| `crons/weekly/etf-cron-timing-tuner__weekly@Mon-07:42:00.md` | Weekly cron-timing tuner schedule |
| `crons/weekly/etf-signal-engine-review__weekly@Fri-17:42:00_user_current.md` | Weekly engine-health review schedule |
| `files/etf-live.html` | The live ETF web app page (working copy) |
| `files/etf-live-bundle.json` | The live app's baked market-data bundle (working copy) |
| `hidden_files/` (51 files) | Past run records: per-slot quote/chart JSONs, widget HTML outputs, helper scripts, the signal state file (`etf_signal_state.json`), the scorecard ledger (`signal_scorecard.json`), and a run log |

### `goals/job-watchdog-for-scheduled-jobs/`
Watches the health of the scheduled jobs and reports only problems.

| File | What it is |
|---|---|
| `GOAL.md` | Notes on the watchdog goal |
| `crons/hourly/job-watchdog__interval@1h.md` | Hourly watchdog schedule |

### `goals/optimal-trading-signal-strategy/`
The strategy backtest research: finding the most reliable signal approach on SPY history.

| File | What it is |
|---|---|
| `GOAL.md` | Notes on the strategy-research goal |
| `agent_notes/2026-09-25/optimal-trading-signal-strategy.md` | Working notes, Sep 25 |
| `agent_notes/2026-09-26/optimal-trading-signal-strategy.md` | Working notes, Sep 26 |
| `agent_notes/2026-09-27/optimal-trading-signal-strategy.md` | Working notes, Sep 27 |
| `files/spy-strategy-backtest-report/spy-strategy-backtest-report.pdf` | The SPY backtest report PDF |
| `files/spy-strategy-backtest-report/.src/` | Report build sources: outline, builder scripts (report, HTML, charts), page source, text source, render records, 10 chart PNGs, validation screenshots |

### `goals/short-video-creation-and-publishing-pipeline/`
The short-video pipeline goal: brand, docs, ledgers, research, and the business plan.

| File | What it is |
|---|---|
| `GOAL.md` | Notes on the short-video pipeline goal |
| `crons/runonce/publish-build-summary-8am__runonce@2026-09-28T08:00:00.md` | One-time publish-summary schedule |
| `files/00-START-HERE.md` | Docs entry point |
| `files/brand/caption-style.md` | Locked caption-style notes |
| `files/brand/profile-bios.md` | Locked profile bios |
| `files/brand/voice-*.mp3` (9 files) | Narrator voice samples — `voice-crisp.mp3` is the locked voice |
| `files/create-and-publish/` (4 files: plan, tasks-balram, tasks-muse, techspec) | Create-and-publish pipeline docs |
| `files/earnings-improvement/` (4 files) | Earnings-improvement pipeline docs |
| `files/housekeeping/` (4 files) | Housekeeping pipeline docs |
| `files/performance-monitoring/` (4 files) | Performance-monitoring pipeline docs |
| `files/promotion/` (4 files) | Promotion pipeline docs |
| `files/ledgers/content-ledger.md` | Content ledger |
| `files/ledgers/sponsor-obligations.md` | Sponsor-obligations ledger |
| `files/reference/` (7 files) | Reference docs: architecture, brand-kit, content-guardrails, decisions-log, monetization-research, platform-policies, topic-engine-scope |
| `files/research/ai-video-niche-research-20260924-2137/` (5 files) | Niche-research report + notes |
| `files/research/creator-sponsorship-affiliate-economics-20260924-2228/` (5 files) | Sponsorship/affiliate research report + notes |
| `files/short-video-project-docs-zip/short-video-project-full.zip` | The docs zip (+ integrity records) |
| `files/short-video-thread-status-board/` | Thread status board PDF + generator sources |
| `hidden_files/business-plan/business-plan-full.md` | Working draft of the business plan |
| `hidden_files/business-plan/research/0*.md` (4 files) | Plan research: market/competition, monetization, platforms, legal/tax |
| `hidden_files/redteam/` (2 files) | Red-team phase-1 findings + report |
| `references/spaces/` (3 files) | Space config references (niche-options, docs-portal, documentation) |

### `goals/sub-3-phev-ev-suv-deal-in-ontario/`
The Ontario PHEV/EV SUV deal scan: daily lease/finance sweep for sub-3% deals.

| File | What it is |
|---|---|
| `GOAL.md` | Notes on the SUV deal-watch goal |
| `agent_notes/2026-09-2*/sub-3-phev-ev-suv-deal-in-ontario.md` (6 files, Sep 22–27) | Daily working notes |
| `crons/daily/phev-ev-suv-deal-watch__daily@08:00:00.md` | Daily deal-scan schedule |
| `crons/daily/phev-ev-suv-payment-watch__daily@08:42:00.md` | Daily payment-watch schedule |
| `files/niro-ev-decision-packet/` | The Niro EV decision packet PDF + build sources and validation |
| `hidden_files/2026-09-2*-scan*.md` (10 files) | Daily scan notes (Kia + non-Kia), Sep 23–28 |

## `imagine_media/`
AI-generated video clips (a "mall evening" short) with thumbnails and the metadata from each generation call.

| File | What it is |
|---|---|
| `imagine_media/media-generation-mall-evening-1-0-*.mp4` | Generated clip 1 |
| `imagine_media/media-generation-mall-evening-2-0-*.mp4` | Generated clip 2 |
| `imagine_media/media-generation-mall-evening-3-0-*.mp4` | Generated clip 3 |
| `imagine_media/.thumbnails/*.jpg` (3 files) | Thumbnails, one per clip |
| `imagine_media/media-generation-mall-evening-*.json` (3 files) | Generation metadata, one per clip |

## `memory/`
Machine-generated memory-reconciliation records — one JSON per reconciliation attempt, grouped by day — plus the reconciler's state file. (Your actual long-term memory lives in `~/memory/`, not here.)

| File | What it is |
|---|---|
| `memory/reconciliation_attempts/2026-09-20/ … 2026-09-28/<id>.json` (33 files) | Per-attempt reconciliation records, one folder per day |
| `memory/reconciliation_state.json` | The reconciler's current state |

## `objectives/`
The agent's own background-study notes.

| File | What it is |
|---|---|
| `objectives/goals/INFERRED_GOAL_LEADS.md` | Notes on inferred goal leads |
| `objectives/goals/STUDYING.md` | Study log for the goals objective |

## `onboarding_tour/`
Screenshots used by the product's onboarding tour.

| File | What it is |
|---|---|
| `onboarding_tour/artifact.png` | Tour screenshot of the Artifacts tab |
| `onboarding_tour/avatars.png` | Tour screenshot of avatars |
| `onboarding_tour/crons.png` | Tour screenshot of scheduled jobs |
| `onboarding_tour/goals.png` | Tour screenshot of the Goals tab |

## `private/`
Chat-private context folders — per-chat records that never leave their chat and are never copied into shared folders.

| File | What it is |
|---|---|
| `private/finance/banking/README.md` | Scope note for the banking chat's private folder |
| `private/finance/taxation/README.md` | Scope note for the taxation chat's private folder |
| `private/health/balram/README.md` | Scope note for your health chat's private folder |

## `repos/`
Local git clones of the six project repos (cloned 2026-09-28) — the live sources of truth that get pushed to GitHub. (`.git` internals excluded below.)

### `repos/bandhu-portal/` — the portal (Cloudflare Worker + pages)
| File | What it is |
|---|---|
| `README.md` | Repo readme |
| `VERSION` | Current version tag |
| `docs/portal-architecture.md` / `.html` / `.pdf` | Portal architecture document (three formats) |
| `public/hub.html` | The portal hub page |
| `public/login.html` | The portal login page (currently dormant) |
| `public/_sess.js` | Session helper script |
| `public/assets/portal.css`, `artifacts.css`, `ev-deals.css` | Portal stylesheets |
| `public/ev-deals/index.html` | The EV deals page |
| `scripts/push_portal.py` | Deploys the portal pages |
| `scripts/push_ev_deals.py` | Deploys the EV deals page |
| `scripts/push_content.py` / `push_content.mjs` | Push content pages (Python / Node) |
| `scripts/seed_users.mjs` | Seeds portal user records |
| `src/worker.mjs` | The Cloudflare Worker source (login + serving) |
| `tests/test_worker.mjs` | Worker auth-flow tests |
| `tests/test_timeout.mjs` | Session-timeout tests |
| `tests/test_public_mode.mjs` | Public-mode behavior tests |
| `wrangler.toml` | Cloudflare deployment config |

### `repos/cross-thread-task-status-tracker/` — the status board + cross-cutting automation
| File | What it is |
|---|---|
| `README.md` | Repo readme |
| `index.html` | The hosted status board page |
| `board.css` | Board stylesheet |
| `tasks.json` | The board's task data |
| `scripts/push_board.py` | Publishes board updates (scripts copy) |
| `scripts/unblock_watch.py` | Unblock-watcher script |
| `scripts/pending_digest.py` | Per-thread task-digest builder |
| `scripts/sync_crons_to_git.py` | Mirrors cron definitions into `crons/` |
| `scripts/pull_all_repos.sh` | Pulls all project repos to latest |
| `scripts/sync_holiday_copies.py` | Validates + mirrors the NYSE holiday JSON |
| `crons/` | Versioned mirror of every saved cron definition |
| `holidays/nyse_holidays.json` | The shared NYSE holiday list |
| `docs/technical/scheduled-jobs.md` | Current list of every scheduled job |
| `docs/workspace-directory-guide.md` | This guide |
| `docs/technical/redesign-spec.md` | Board redesign specification |
| `artifacts/index.html` | The Artifact Index page |
| `tests/synthetic_matrix.js` | Board test matrix |
| `hidden_files/task_status_snapshot.json` | Last-known task statuses |
| `hidden_files/unblock_watch_state.json` | Watcher state |

### `repos/short-video/` — short-video docs, plans, and media
| File | What it is |
|---|---|
| `README.md` | Repo readme |
| `docs/00-START-HERE.html`, `docs/index.html` | Docs entry page + home |
| `docs/Short-Video-Comprehensive-Business-Plan.docx` | The business plan |
| `docs/Short-Video-Business-Model-Risk-Register.docx` | The risk register |
| `docs/short-video-thread-status-board.pdf` | Thread status board PDF |
| `docs/create-and-publish/`, `docs/earnings-improvement/`, `docs/housekeeping/`, `docs/performance-monitoring/`, `docs/promotion/` (4 HTML files each) | Pipeline plans, task lists, tech specs |
| `docs/plans/create-and-publish/`, `docs/plans/promotion/` (4 markdown files each) | Markdown versions of the pipeline docs |
| `docs/reference/` (7 HTML files) | Architecture, brand-kit, content-guardrails, decisions-log, monetization-research, platform-policies, topic-engine-scope |
| `docs/ledgers/content-ledger.html`, `docs/ledgers/sponsor-obligations.html` | Content + sponsor ledgers |
| `docs/research/` (10 HTML files) | Niche-research and sponsorship/affiliate research |
| `docs/diagrams/diag-*.png` (16 files) | Architecture/flow diagrams (auth, publish, Meta, TikTok, X, YouTube) |
| `docs/*.pdf`, `docs/*.md` (10 files) | Platform overview + technical-architecture docs (Meta, TikTok, X, YouTube, general) |
| `artifacts/brand/voice-*.mp3` (4 files) | Narrator voice samples |
| `artifacts/short-video-project-full.zip` | The full project zip |
| `web-exports/niche-options.html`, `web-exports/short-video-project-documentation.html` | Page exports |

### `repos/trading/` — ETF signal engine + alert builders
| File | What it is |
|---|---|
| `README.md` | Repo readme |
| `VERSION` | Current version tag |
| `docs/signal-engine-technical.md` / `signal-engine-plain-words.md` | Signal-engine docs (technical + plain-words) |
| `docs/etf-alert-builder-technical.md` / `etf-alert-builder-plain-words.md` | Alert-builder docs (technical + plain-words) |
| `reports/spy-strategy-backtest-report.pdf` | SPY backtest report |
| `src/build_widget.py` | Builds the ETF alert widget (cards + charts) |
| `src/build_signals.py` | The BUY/SELL/HOLD signal engine |
| `src/build_scorecard.py` | Grades published signals against their targets |
| `src/build_live_bundle.py` | Bakes fresh market data into the live page |
| `src/build_and_send_email.py` | Builds/sends the alert email (currently disabled) |
| `src/review_engine.py` | Weekly engine-health review script |
| `src/econ_events.json` | Verified CPI/PPI/FOMC/jobs dates |

### `repos/trading-portal/` — the live ETF web app
| File | What it is |
|---|---|
| `README.md` | Repo readme (branches, holiday flow, deploy process) |
| `etf-live.html` | The live ETF web app page |
| `etf-live.css` | Its stylesheet |
| `etf-live-bundle.json` | Its baked market-data bundle |
| `nyse-holidays.json` | The assembled NYSE holiday file the page loads (deploy-time only) |
| `scripts/deploy_portal.py` | Assembles + deploys the `gh-pages` branch (validates the holiday JSON) |
| `tests/` | Portal regression suite |

### `repos/vehicle/` — vehicle project
| File | What it is |
|---|---|
| `README.md` | Repo readme |
| `niro-ev-decision-packet.pdf` | The Niro EV decision packet |

## `scheduler/`
Empty placeholder directory — no files, no active use.

## `self_improvement/`
The agent's background self-improvement loop: per-objective state files (a `CURRENT.md` plus daily archives) and per-run staging sandboxes. Entirely machine-generated.

| File | What it is |
|---|---|
| `self_improvement/objectives/<10 objectives>/CURRENT.md` | Each objective's current state (alignment, goals_bookkeeping, ideas, memory, proactive_notifier, relationships, shopping, skill_improvement, studying, urgency_classifier) |
| `self_improvement/objectives/<each>/archive/<timestamp>.CURRENT.md` (~130 files) | Daily snapshots of each objective's state |
| `self_improvement/staging/memory/sirun_<id>/memory_reconciliation/pinned/MEMORY.numbered.md` (~99 files) | Per-run numbered memory snapshots |
| `self_improvement/staging/memory/sirun_<id>/memory_reconciliation/pinned/MEMORY.pinned.md` (~99 files) | Per-run pinned memory snapshots |
| `self_improvement/staging/memory/sirun_<id>/memory_reconciliation/reconciliation_state.json` (~100 files) | Per-run reconciliation state |
| `self_improvement/staging/shopping/sirun_<id>/shopping/PROFILE.md` (3 files) | Per-run shopping profiles (+ promotion records) |
| `self_improvement/staging/studying/sirun_<id>/agent_notes/<date>/goal_<id>.md` (9 files) | Per-run studying notes |
| `self_improvement/migrations/copy_first_objective_workspace_v1.json` | One-time migration record |
| `self_improvement/relationships/legacy_page_archives/` | Present but empty |

## `shared/`
The shared context library in three layers — global (all chats), per-category (health, finance, trading, vehicle) — plus templates for new categories. READMEs only so far.

| File | What it is |
|---|---|
| `shared/README.md` | Explains the three context layers |
| `shared/global/README.md` | Scope note for the global layer |
| `shared/global/templates/new-category-template.md` | Template for creating a new category/chat |
| `shared/finance/README.md` | Scope note for the finance layer |
| `shared/health/README.md` | Scope note for the health layer |
| `shared/trading/README.md` | Scope note for the trading layer |
| `shared/vehicle/README.md` | Scope note for the vehicle layer |
| `shared/holidays/nyse_holidays.json` | The canonical NYSE holiday list (workspace copy; mirrored to the cross-thread repo) |

## `short-video/`
Short-video pipeline working files: intro-video build assets, doc-build scratch scripts, and publish-pipeline build notes.

| File | What it is |
|---|---|
| `short-video/docbuild-scratch/md2pdf.py` | Converts markdown docs to PDF |
| `short-video/docbuild-scratch/meta-overview.md` | Meta overview doc source |
| `short-video/docbuild-scratch/overview.md` | General overview doc source |
| `short-video/docbuild-scratch/tiktok-overview.md` | TikTok overview doc source |
| `short-video/docbuild-scratch/x-overview.md` | X overview doc source |
| `short-video/docbuild-scratch/youtube-overview.md` | YouTube overview doc source |
| `short-video/docbuild-scratch/push_docs_repo.py` | Pushes docs into the short-video repo |
| `short-video/docbuild-scratch/push_docs_update.py` | Pushes doc updates |
| `short-video/intro/build.sh` | Assembles the intro video |
| `short-video/intro/intro-final.mp4` | Final intro video |
| `short-video/intro/intro-raw.mp4` | Raw intro video |
| `short-video/intro/scene1.mp4` … `scene4.mp4` | Intro scene clips |
| `short-video/intro/vo-p1.mp3` … `vo-p4.mp3` | Intro voiceover parts |
| `short-video/intro/cover.jpg` | Intro cover frame |
| `short-video/intro/check-s1.jpg`, `check-s4.jpg` | Scene check frames |
| `short-video/intro/media-generation-intro-scene*-*.webp` (4 files) | Generated intro scene images |
| `short-video/intro/media-generation-intro-scene*-*.json` (4 files) | Their generation metadata |
| `short-video/publish-build/SUMMARY.md` | Publish-pipeline build summary |
| `short-video/publish-build/meta-BUILD.md` | Meta publish build notes |
| `short-video/publish-build/tiktok-BUILD.md` | TikTok publish build notes |
| `short-video/publish-build/x-BUILD.md` | X publish build notes |
| `short-video/publish-build/youtube-BUILD.md` | YouTube publish build notes |

## `skills/`
Workspace skills — reusable playbooks. Each skill has a `SKILL.md` guide and API helper scripts in `bin/`.

| File | What it is |
|---|---|
| `skills/cloudflare/SKILL.md` | Cloudflare skill guide |
| `skills/cloudflare/bin/cf_api.py` | Cloudflare API helper script |
| `skills/github/SKILL.md` | GitHub skill guide |
| `skills/github/bin/gh_api.py` | GitHub REST API helper script |
| `skills/github/bin/validate_token.py` | Read-only GitHub token validator |
| `skills/meta-publish/SKILL.md` | Meta (Facebook/Instagram) publishing skill guide |
| `skills/meta-publish/TEST_DESIGN.md` | How its publish tests are designed |
| `skills/meta-publish/bin/meta_api.py` | Meta Graph API helper script |
| `skills/meta-publish/bin/fb_publish_video.py` | Publishes a video to Facebook |
| `skills/meta-publish/bin/ig_publish_reel.py` | Publishes a reel to Instagram |
| `skills/meta-publish/bin/ig_check_token.py` | Checks the Instagram token/permissions |
| `skills/resend/SKILL.md` | Resend email skill guide |
| `skills/resend/bin/resend_api.py` | Resend API helper script |
| `skills/tiktok-publish/SKILL.md` | TikTok publishing skill guide |
| `skills/tiktok-publish/MECHANISM.md` | TikTok Content Posting API mechanism notes |
| `skills/tiktok-publish/TEST_DESIGN.md` | How its publish tests are designed |
| `skills/tiktok-publish/bin/tiktok_publish.py` | TikTok publish helper script |
| `skills/x-publish/SKILL.md` | X publishing skill guide |
| `skills/x-publish/MECHANISM.md` | X API mechanism notes |
| `skills/x-publish/DORMANT.md` | Notes that X publishing is dormant (defensive handle only) |
| `skills/x-publish/TEST_DESIGN.md` | How its publish tests are designed |
| `skills/x-publish/bin/x_publish_video.py` | X video-post helper script |
| `skills/youtube-publish/SKILL.md` | YouTube publishing skill guide |
| `skills/youtube-publish/TEST_DESIGN.md` | How its publish tests are designed |
| `skills/youtube-publish/bin/youtube_upload.py` | YouTube Shorts uploader script |
| `skills/youtube-publish/bin/oauth_flow.py` | Google OAuth flow helper script |
| `skills/youtube-publish/bin/token_store.py` | OAuth token storage helper |
| `skills/<each>/bin/__pycache__/*.pyc` (11 files) | Compiled Python caches (machine-generated) |

## `space_data/`
Preview/thumbnail image sets auto-generated for web spaces — share cards, screenshots, and thumbnails used when sharing links.

| File | What it is |
|---|---|
| `space_data/all-threads-status-board/.previews/<2 runs>/` (8 files + current.json) | Share card, preview card, source screenshot, thumbnail — two runs |
| `space_data/niche-options/.previews/<run>/` (4 files + current.json) | Share card, preview card, source screenshot, thumbnail |
| `space_data/short-video-docs-portal/.previews/<2 runs>/` (12 files + current.json) | Run reports, full-page screenshots, share/preview cards, thumbnails — two runs |
| `space_data/short-video-project-documentation/.previews/<run>/` (4 files + current.json) | Share card, preview card, source screenshot, thumbnail |

## `spaces/`
Empty placeholder directory — no files, no active use.

## `ts-spaces/`
Legacy web-app ("spaces") build area: five spaces with their source pages, plus machine-generated build audits, compiled build outputs, harness files, and caches.

| File | What it is |
|---|---|
| `ts-spaces/all-threads-status-board/` (index.html, space.json, AGENTS.md, icon.jpg) | The status board space page source + config |
| `ts-spaces/thread-status-board/` (4 files) | The older thread board space page source + config |
| `ts-spaces/niche-options/` (4 files) | The niche-options space page source + config |
| `ts-spaces/short-video-project-documentation/` (4 files + assets/) | The documentation space page source + config; assets hold the project zip + 4 voice samples |
| `ts-spaces/short-video-docs-portal/` | The docs portal app: agent notes, data plan, configs, frontend source (`client/src/`), compiled frontend (`client/dist/`), backend source + compiled (`server/`), database migrations (`drizzle/`), its SQLite database (`app.db`) |
| `ts-spaces/<space>/audits/<run>/…` (185 files) | Machine-generated build audit logs across the five spaces |
| `ts-spaces/<space>/.space-build*/…` (31 files) | Machine-generated compiled build outputs |
| `ts-spaces/<space>/.harness/…` (17 files) | Machine-generated test-harness files |
| `ts-spaces/short-video-docs-portal/.bun-cache/…` (23 files) | Machine-generated bun package cache |

## `user/`
Files handed over by you (numbered uploads) plus cached browser screenshots from the media library.

| File | What it is |
|---|---|
| `user/files/44337_0_9d5x.png` … `user/files/45986_2_6lp1.png` (46 files) | Your uploaded images, named by upload ID |
| `user/media_library/browser_screenshots/*/*.png` (4 files) | Cached browser screenshots |

## `verifier/`
The independent QC/verification gate: the actual procedure plus the visible failure log.

| File | What it is |
|---|---|
| `verifier/CHECKLIST.md` | The verifier/QC pipeline procedure — the permanent gate every research result, artifact, and quantitative deliverable must pass |
| `verifier/failures.md` | The failure log — visible track record of failures that reached you, with post-mortems |

## `voice_notes/`
Voice-note audio.

| File | What it is |
|---|---|
| `voice_notes/readout-2026-09-26.mp3` | An audio readout from 2026-09-26 |

## `your_files/`
User-facing deliverables — the file area behind the Artifacts tab: documents, videos, and exported web pages.

| File | What it is |
|---|---|
| `your_files/all-threads-status-board/all-threads-status-board.html` | Exported status board page |
| `your_files/niche-options/niche-options.html` | Exported niche-options page |
| `your_files/short-video-project-documentation/short-video-project-documentation.html` | Exported documentation page |
| `your_files/etf-live.html` / `your_files/etf-live.css` | The ETF live app page + stylesheet (older copy) |
| `your_files/mall-evening-short.mp4` | Generated short video (v1) |
| `your_files/mall-evening-short-v2.mp4` | Generated short video (v2) |
| `your_files/mall-evening-short-v3.mp4` | Generated short video (v3) |
| `your_files/short-video-comprehensive-business-plan/Short-Video Comprehensive Business Plan.docx` | The business-plan document |
| `your_files/short-video-comprehensive-business-plan/.src/` | Plan build sources: outline, generator script, URL baseline, validation report, validation PDF, 49 page screenshots, 13 sheet screenshots |
| `your_files/short-video-business-model-risk-register/Short-Video Business Model Risk Register.docx` | The risk-register document |
| `your_files/short-video-business-model-risk-register/.src/` | Register build sources: outline, builder script, URL baseline, build transcripts, validation artifacts |
| `your_files/workspace-directory-guide/workspace-directory-guide.md` | This guide |

## Hidden directories

| Directory | What it's for |
|---|---|
| `.hatch-browser/` (1,969 files) | Browser session snapshots (page contents, accessibility trees) — machine-generated cache; files not itemized |
| `.docbuild-venv/` (1,765 files) | Python virtual environment used for document building — machine-generated; files not itemized |
| `.jarvis/idea-executions/a21eb261-…/scratch/precon_digest_state.json` | Scratch state from an idea execution (precon-digest run) |

## Loose files at the workspace root

| File | What it is |
|---|---|
| `credential_handoff_checklist.md` | Trigger-bound checklist that must be read before proposing or requesting any credential, token, or secret in chat — secure flow first, never ask for raw values in chat, map production storage before any handoff |
| `short-video-project.zip` | The short-video project documentation zip (2026-09-25), kept at root for sharing |

---

*End of guide. Counts were verified against the live filesystem on 2026-09-28 ~11:55 EDT, after the ~11:52 EDT restructure.*
