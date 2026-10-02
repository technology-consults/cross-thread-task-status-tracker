#!/usr/bin/env python3
"""Unit + functional tests for the chat-sweep PDF digest builder.

The builder lives with the goal's operational scripts:
    ~/workspace/goals/all-threads-status-board-upkeep/hidden_files/sweep_digest_pdf.py
This test file lives in the board repo so it runs in the unit tier
(tests/run_unit.py) and gates every commit via scripts/commit.py.

The builder renders with pageCompression=0 on purpose, so these tests can
verify PDF content by plain string search — no PDF parser needed.

Convention: a main() printing "<N> passed, <M> failed", exit 0 on
success, 1 on failure.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HOME = os.path.expanduser("~")
BUILDER = os.path.join(
    HOME, "workspace/goals/all-threads-status-board-upkeep/"
    "hidden_files/sweep_digest_pdf.py")

_passed = 0
_failed = 0


def check(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1
    else:
        _failed += 1
    print(f"{'PASS' if cond else 'FAIL'}: {name}"
          + (f" — {detail}" if detail and not cond else ""))


def load_builder():
    spec = importlib.util.spec_from_file_location("sweep_digest_pdf", BUILDER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SAMPLE = {
    "run_date": "2026-10-02",
    "generated_at": "2026-10-02 10:42 EDT",
    "missed_or_attention": [
        {"title": "Trading verdicts not filed",
         "detail": "4 verdicts said in-chat, missing from tasks.json",
         "where": "Trading · 2026-10-01"}
    ],
    "tasks_created": [
        {"title": "tr.review-2001", "status": "done",
         "thread": "Trading", "due": ""},
        {"title": "tr.archive-blindspot-sweep", "status": "parked",
         "thread": "Trading", "due": "2026-10-05"},
    ],
    "decisions": [
        {"text": "Driving-mode default: concise bullets, large font",
         "where": "Main · 2026-10-02"}
    ],
}


def pdf_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("latin-1")


def main():
    check("builder script exists", os.path.exists(BUILDER), BUILDER)
    if not os.path.exists(BUILDER):
        print(f"\n{_passed} passed, {_failed} failed")
        return 1
    mod = load_builder()

    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "digest.pdf")
        summary = mod.build_digest_pdf(SAMPLE, out)

        # --- unit: summary + file validity ---
        check("summary counts",
              summary["missed"] == 1 and summary["tasks"] == 2
              and summary["decisions"] == 1, str(summary))
        check("summary pages >= 1", summary["pages"] >= 1)
        check("output exists and non-empty",
              os.path.exists(out) and summary["bytes"] > 1000)
        with open(out, "rb") as fh:
            check("valid PDF header", fh.read(5) == b"%PDF-")

        text = pdf_text(out)
        # --- unit: required content ---
        check("title + run date", "Chat Sweep Digest" in text
              and "2026-10-02" in text)
        check("creation timestamp present", "Created:" in text)
        check("last-modified timestamp present", "Last modified:" in text)
        check("section: missed", "Missed / needs attention" in text)
        check("section: tasks", "Tasks created / filed this run" in text)
        check("section: decisions", "Key decisions" in text)
        check("missed item text", "Trading verdicts not filed" in text)
        check("task row text",
              "tr.review-2001" in text and "tr.archive-blindspot-sweep" in text)
        check("decision text", "Driving-mode default" in text)
        check("footer page number", "page 1" in text)

        # --- unit: empty sections ---
        out2 = os.path.join(tmp, "empty.pdf")
        summary2 = mod.build_digest_pdf({"run_date": "2026-10-03"}, out2)
        text2 = pdf_text(out2)
        check("empty input builds",
              summary2["missed"] == 0 and os.path.getsize(out2) > 500)
        check("empty sections say None this run",
              text2.count("None this run") == 3, text2.count("None this run"))
        check("timestamps present even when empty",
              "Created:" in text2 and "Last modified:" in text2)

        # --- functional: CLI end-to-end ---
        jin = os.path.join(tmp, "in.json")
        out3 = os.path.join(tmp, "cli.pdf")
        with open(jin, "w", encoding="utf-8") as fh:
            json.dump(SAMPLE, fh)
        r = subprocess.run([sys.executable, BUILDER,
                            "--input", jin, "--output", out3],
                           capture_output=True, text=True, timeout=60)
        check("CLI exit 0", r.returncode == 0, r.stderr[:200])
        check("CLI produced valid PDF",
              os.path.exists(out3) and pdf_text(out3).startswith("%PDF-"))
        check("CLI stdout summary", "PDF digest:" in r.stdout)

    print(f"\n{_passed} passed, {_failed} failed")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
