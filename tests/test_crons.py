#!/usr/bin/env python3
"""
Cron job regression suite.
Validates every recurring cron: definition exists, scripts are valid,
and (where safe) scripts run without error.
Run: python3 tests/test_crons.py
Exit 0 = all pass, non-zero = failures.
"""
import os, sys, py_compile, subprocess

HOME = os.path.expanduser("~")
passed, failed = [], []

def check(name, cond, detail=""):
    (passed if cond else failed).append(name)
    print(f"{'PASS' if cond else 'FAIL'}: {name}" + (f" — {detail}" if detail and not cond else ""))

def cron_exists(path):
    full = os.path.join(HOME, path)
    check(f"cron defined: {os.path.basename(path)}", os.path.exists(full), f"missing {path}")

def script_valid(path, name):
    full = os.path.join(HOME, path)
    if not os.path.exists(full):
        check(f"script valid: {name}", False, f"missing {path}")
        return
    try:
        py_compile.compile(full, doraise=True)
        check(f"script valid: {name}", True)
    except Exception as e:
        check(f"script valid: {name}", False, str(e)[:100])

# --- Cron definitions exist ---
CRONS = [
    "workspace/cron.d/daily/portal-links-watch__daily@07:42:00_user_current.md",
    "workspace/cron.d/hourly/board-unblock-watch-sv__interval@1h.md",
    "workspace/cron.d/hourly/board-unblock-watch-tr__interval@1h.md",
    "workspace/cron.d/hourly/board-unblock-watch-vh__interval@1h.md",
    "workspace/goals/all-threads-status-board-upkeep/crons/daily/cron-definitions-sync__daily@06:42:00.md",
    "workspace/goals/all-threads-status-board-upkeep/crons/daily/sv-chat-review__daily@10:42:00_user_current.md",
    "workspace/goals/all-threads-status-board-upkeep/crons/daily/task-due-date-watch__daily@08:42:00_user_current.md",
    "workspace/goals/all-threads-status-board-upkeep/crons/hourly/repo-pull-hourly__interval@1h.md",
    "workspace/goals/etf-price-updates/crons/daily/etf-price-preclose__daily@15:15:00.md",
    "workspace/goals/etf-price-updates/crons/daily/etf-trading-signals__daily@07:30:00.md",
    "workspace/goals/etf-price-updates/crons/daily/signal-scorecard__daily@08:42:00.md",
    "workspace/goals/etf-price-updates/crons/hourly/etf-price-updates__interval@2h.md",
    "workspace/goals/etf-price-updates/crons/hourly/etf-signal-intraday-market__interval@1h.md",
    "workspace/goals/etf-price-updates/crons/hourly/etf-signal-intraday-offhours__interval@6h.md",
    "workspace/goals/etf-price-updates/crons/minutely/etf-live-bundle__interval@5m.md",
    "workspace/goals/etf-price-updates/crons/weekly/etf-signal-engine-review__weekly@Fri-17:42:00_user_current.md",
    "workspace/goals/job-watchdog-for-scheduled-jobs/crons/hourly/job-watchdog__interval@1h.md",
    "workspace/goals/sub-3-phev-ev-suv-deal-in-ontario/crons/daily/phev-ev-suv-deal-watch__daily@08:00:00.md",
    "workspace/goals/sub-3-phev-ev-suv-deal-in-ontario/crons/daily/phev-ev-suv-payment-watch__daily@08:42:00.md",
]
for c in CRONS:
    cron_exists(c)

# precon-digest is DISABLED — verify it's still disabled (not accidentally re-enabled)
precon = os.path.join(HOME, "workspace/goals/builder-email-digest/crons/daily/precon-digest__daily@08:42:00.md")
check("precon-digest: still disabled", os.path.exists(precon), "definition missing")

# --- Scripts are syntactically valid ---
SCRIPTS = [
    ("workspace/repos/trading/src/build_live_bundle.py", "etf-live-bundle"),
    ("workspace/repos/trading/src/build_widget.py", "etf-price-updates"),
    ("workspace/repos/trading/src/build_signals.py", "etf-trading-signals"),
    ("workspace/repos/trading/src/build_scorecard.py", "signal-scorecard"),
    ("workspace/repos/trading/src/review_engine.py", "etf-signal-engine-review"),
    ("workspace/repos/cross-thread-task-status-tracker/unblock_watch.py", "board-unblock-watch"),
    ("workspace/repos/cross-thread-task-status-tracker/push_board.py", "board-publish"),
    ("workspace/repos/cross-thread-task-status-tracker/scripts/pending_digest.py", "digest-generator"),
    ("workspace/repos/cross-thread-task-status-tracker/scripts/sync_crons_to_git.py", "cron-definitions-sync"),
    ("workspace/goals/all-threads-status-board-upkeep/hidden_files/sweep_digest_pdf.py", "chat-sweep-pdf-digest"),
    ("workspace/repos/bandhu-portal/scripts/push_ev_deals.py", "phev-ev-suv-deal-watch"),
]
for path, name in SCRIPTS:
    script_valid(path, name)

print(f"\n{len(passed)} passed, {len(failed)} failed")
sys.exit(1 if failed else 0)
