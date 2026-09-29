#!/usr/bin/env python3
"""Two task digests for one board thread (2026-09-28 redesign).

Reads tasks.json and produces, per thread:
- Digest 1 "Action needed": todo, pending_review, blocked, blocked_discuss,
  pending_review_post_discussion, not_approved.
- Digest 2 "In flight & settled": in_progress, parked, approved, done,
  blocked_completed, blocked_approved.
(completed and rejected appear in neither.)

Prints both as markdown tables to stdout (for the tracker-thread message) and
writes one landscape PDF per digest to
~/workspace/your_files/task-tracker-digests/<project>/ with stable filenames
(<project>-digest1-latest.pdf, <project>-digest2-latest.pdf), deleting older
copies so only the latest of each lives on.

Columns: Task | Summary | Status | Assigned | Created | Due.
Summary is extracted dynamically from the task's detail text (first meaningful
line, bullets stripped, truncated). Owner comes from the board's assigned_to
field; a (yours) in the title is the fallback for tasks that predate it.

Usage: pending_digest.py --thread sv|tr|vh
Run with the docbuild venv python (has reportlab):
  ~/workspace/.docbuild-venv/bin/python scripts/pending_digest.py --thread tr
"""
import argparse
import glob
import html
import json
import os
import re
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS_JSON = os.path.join(REPO, "tasks.json")
OUT_BASE = os.path.expanduser("~/workspace/your_files/task-tracker-digests")
TZ = ZoneInfo("America/Toronto")

THREADS = {"sv": "short-video", "tr": "trading", "vh": "vehicle"}
THREAD_TITLES = {"sv": "Short Video", "tr": "Trading", "vh": "Vehicle"}

# Board STATUS map (labels + sort ranks), from index.html.
STATUS = {
    "blocked":                      {"label": "Blocked",                 "rank": 1},
    "blocked_discuss":              {"label": "Blocked — discussing",    "rank": 2},
    "pending_review":               {"label": "Pending review",          "rank": 3},
    "pending_review_post_discussion": {"label": "Review — clarifying",   "rank": 4},
    "not_approved":                 {"label": "Not approved — rework",   "rank": 5},
    "todo":                         {"label": "To-do",                   "rank": 6},
    "in_progress":                  {"label": "In progress",             "rank": 7},
    "blocked_completed":            {"label": "Finished — awaiting review", "rank": 8},
    "blocked_approved":             {"label": "Blocked — then approved", "rank": 9},
    "approved":                     {"label": "Approved",                "rank": 10},
    "parked":                       {"label": "Parked",                  "rank": 11},
    "completed":                    {"label": "Completed — wrapping up", "rank": 12},
    "done":                         {"label": "Done",                    "rank": 13},
    "rejected":                     {"label": "Rejected",                "rank": 14},
}

DIGEST1 = ("todo", "pending_review", "blocked", "blocked_discuss",
           "pending_review_post_discussion", "not_approved")
DIGEST2 = ("in_progress", "parked", "approved", "done",
           "blocked_completed", "blocked_approved")
# completed + rejected appear in neither digest.

BULLET = re.compile(r"^[\s•\-\*\u2013\u2014\d\.\)\]]+")
WS = re.compile(r"\s+")


def summarize(detail, limit=140):
    """First meaningful line of the detail text, bullets stripped."""
    if not detail:
        return "—"
    for line in str(detail).splitlines():
        line = WS.sub(" ", BULLET.sub("", line)).strip()
        if line:
            return line if len(line) <= limit else line[: limit - 1].rstrip() + "…"
    return "—"


def owner_of(t):
    a = t.get("assigned_to")
    if a in ("BalRam", "Bandhu"):
        return a
    if "(yours)" in (t.get("title") or "").lower():
        return "BalRam"
    return "—"


def load_tasks(thread, which):
    with open(TASKS_JSON) as f:
        data = json.load(f)
    tasks = data["tasks"] if isinstance(data, dict) else data
    sel = [t for t in tasks if t.get("thread") == thread and t.get("status") in which]
    sel.sort(key=lambda t: (STATUS.get(t.get("status"), {}).get("rank", 99),
                            t.get("due") or "9999",
                            t.get("title") or ""))
    return sel


def row_of(t):
    st = STATUS.get(t.get("status"), {"label": t.get("status")})
    return {
        "title": t.get("title") or t.get("id", ""),
        "summary": summarize(t.get("detail")),
        "status": st["label"],
        "owner": owner_of(t),
        "created": t.get("created") or "—",
        "due": t.get("due") or "—",
    }


def md_table(rows):
    lines = ["| Task | Summary | Status | Assigned | Created | Due |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        cells = [r[k].replace("|", "\\|") for k in
                 ("title", "summary", "status", "owner", "created", "due")]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def build_pdf(rows, project, title_name, digest_no, digest_name, created):
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    Table, TableStyle)

    fname = f"{project}-digest{digest_no}-latest.pdf"
    outdir = os.path.join(OUT_BASE, project)
    os.makedirs(outdir, exist_ok=True)
    for old in glob.glob(os.path.join(outdir, f"{project}-digest{digest_no}-*.pdf")):
        if os.path.basename(old) != fname:
            os.remove(old)
    path = os.path.join(outdir, fname)

    ACCENT = colors.HexColor("#1a5fb4")
    DARK = colors.HexColor("#1e1e1e")
    GREY = colors.HexColor("#5a5a5a")
    PAGE = landscape(A4)

    def P(text, **kw):
        base = dict(fontName="Helvetica", fontSize=8.5, leading=11.5,
                     textColor=DARK, alignment=TA_LEFT)
        base.update(kw)
        return Paragraph(text, ParagraphStyle("c", **base))

    story = []
    story.append(Paragraph(f"{title_name} — {digest_name}",
                           ParagraphStyle("t", fontName="Helvetica-Bold",
                                          fontSize=18, leading=22,
                                          textColor=ACCENT, spaceAfter=4)))
    story.append(Paragraph(
        f"Created {created.strftime('%Y-%m-%d %H:%M %Z')} · {len(rows)} task(s)",
        ParagraphStyle("s", fontName="Helvetica", fontSize=9.5, leading=13,
                       textColor=GREY, spaceAfter=10)))
    if rows:
        hdr = [P("<b>Task</b>"), P("<b>Summary</b>"), P("<b>Status</b>"),
               P("<b>Assigned</b>"), P("<b>Created</b>"), P("<b>Due</b>")]
        body = [[P(html.escape(r["title"])), P(html.escape(r["summary"])),
                 P(html.escape(r["status"])), P(html.escape(r["owner"])),
                 P(html.escape(r["created"])), P(html.escape(r["due"]))]
                for r in rows]
        # landscape A4 usable width ~257mm after margins
        widths = [42 * mm, 88 * mm, 38 * mm, 24 * mm, 28 * mm, 28 * mm]
        tbl = Table([hdr] + body, colWidths=widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f2f5fa")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d4e8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)
    else:
        story.append(P("Nothing in this digest — all clear.", fontSize=11))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Summary is the first line of each task's board detail text. "
        "Assigned comes from the board's assigned-to field.",
        ParagraphStyle("n", fontName="Helvetica-Oblique", fontSize=8,
                       leading=11, textColor=GREY)))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GREY)
        canvas.drawCentredString(PAGE[0] / 2, 12 * mm,
                                 f"Created {created.strftime('%Y-%m-%d %H:%M %Z')} · page {doc.page}")
        canvas.restoreState()

    SimpleDocTemplate(path, pagesize=PAGE,
                      leftMargin=15 * mm, rightMargin=15 * mm,
                      topMargin=14 * mm, bottomMargin=16 * mm,
                      title=f"{title_name} {digest_name.lower()}",
                      ).build(story, onFirstPage=footer, onLaterPages=footer)
    # sweep any stray non-latest copies of this digest
    for old in glob.glob(os.path.join(outdir, f"{project}-digest{digest_no}-*.pdf")):
        if old != path:
            os.remove(old)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thread", required=True, choices=("sv", "tr", "vh"))
    args = ap.parse_args()
    project = THREADS[args.thread]
    title_name = THREAD_TITLES[args.thread]
    created = datetime.now(TZ)

    digests = [
        (1, "Digest 1 — Action needed", DIGEST1),
        (2, "Digest 2 — In flight & settled", DIGEST2),
    ]
    pdf_paths = []
    for no, name, which in digests:
        rows = [row_of(t) for t in load_tasks(args.thread, which)]
        print(f"## {title_name} — {name} ({len(rows)})")
        print(f"Created: {created.strftime('%Y-%m-%d %H:%M %Z')}")
        print()
        if rows:
            print(md_table(rows))
        else:
            print("Nothing in this digest — all clear.")
        print()
        pdf_paths.append(build_pdf(rows, project, title_name, no, name, created))

    for i, p in enumerate(pdf_paths, 1):
        print(f"PDF_PATH_DIGEST{i}: {p}")


if __name__ == "__main__":
    main()
