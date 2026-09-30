---
id: phev-ev-suv-payment-watch
title: EV payment-only watch (Ontario)
enabled: true
owner: goal:sub-3-phev-ev-suv-deal-in-ontario
mode: task
schedule:
  alignment: aligned
  at: null
  catchup: latest
  dom: []
  dow: []
  every: null
  kind: daily
  month: []
  time: 08:42:00
  timezone: America/Toronto
delivery:
- chat_id: de5d7ab8-9709-4e7c-a556-fd5f582b2f7e
execution:
  kind: agent
retry:
  max_retries: 0
  on_failure: false
timeout_secs: null
schedule_key: daily@08:42:00
path: /home/hatch/workspace/goals/sub-3-phev-ev-suv-deal-in-ontario/crons/daily/phev-ev-suv-payment-watch__daily@08:42:00.md
is_heartbeat: false
is_system: false
---
WORKER CONDUCT (mandatory — read first):
Do ALL research in this run yourself with your own tools: web search, page fetch/open, live browser tasks for site navigation and payment-calculator configuration, shell commands for local scripts, widget tools for the HTML panel, chat/artifact tools for delivery. NEVER spawn subagents and NEVER delegate any part of this run to another agent: the scheduler-side worker has no durable chat owner for subagent follow-ups, and delegating kills the run ("failed while waiting for descendant subagents before resolution: follow-up has no durable chat owner") before any report is produced. This exact failure killed the 2026-09-29 morning run. If the work feels like a lot for one pass, break it into sequential tool calls yourself — do not hand it off.

Payment-only EV SUV watch for BalRam (Ontario). This is the afternoon sibling of the 08:00 EV deal scan: it cares ONLY about the bi-weekly PAYMENT, and flags anything cheap — not just what's under a headline rate.

TARGETS: 48-month LEASE bi-weekly ≤ $265 (tax-included, $5,000 down, 20,000 km/yr) OR 72-month FINANCE bi-weekly ≤ $365 (tax-included, $5,000 down). Payment computed on the real transaction: net price after manufacturer rebates and any eligible federal EVAP, then $5,000 down.

LOYALTY RATES (standing user rule): BalRam qualifies for Kia loyalty ONLY. Kia vehicles may use loyalty-reduced rates — state the reduction explicitly (e.g. 4.49% → 3.49% with the 1-pt Kia loyalty cut). For ALL other manufacturers, use only the publicly advertised non-loyalty rate; if a brand's advertised rate bakes in a loyalty reduction (e.g. Hyundai's bake in 1%), report the standard non-loyalty rate instead, or flag the candidate as rate-unverified. Mazda's advertised lease rates are already the non-loyalty rate.

CONTEXT: Federal EVAP (verified 2026-09-29 against Transport Canada): up to $5,000 BEV / $2,500 PHEV in 2026, final transaction value ≤ $50,000 (no cap for Canadian-made EVs); steps down each Jan 1 from 2027. Applied at point of sale; minimum 12-month lease, 48-month lease earns the full amount. Fold the rebate into the reported figures when the manufacturer's own calculator applies it (Kia's EV-rebate checkbox); if the calculator has no such option, subtract the eligible amount explicitly. Always show pre-EVAP net price alongside the post-EVAP headline. Above the $50,000 cap or otherwise ineligible: show WITHOUT the rebate and one-line why — never force it. Ontario has no provincial rebate. EVs ONLY (2026-09-28 rule change — no PHEVs, no hybrids).

METHOD: Check manufacturer offer pages and GTA/Ontario dealer mirrors (Hyundai, Kia, Toyota, Mitsubishi, Mazda, Subaru, Honda, Ford, Chevrolet, VW, Nissan) — EVs only. Verify every URL by opening it — never invent URLs. Every rate, MSRP, rebate, and payment figure must come from a page opened during THIS run — never carry a figure forward from a previous run; if a page is unreachable, mark the candidate unverified. Every program cited must be confirmed Canadian/Ontario — US/Korean/EU programs are never presented as Canadian; ambiguous market → label unconfirmed. Confirm measurement standards match when comparing specs across sources (EPA vs WLTP vs NRCan etc.); label inferences as inferences.

LINKS (standing user rule): navigate the manufacturer site, select Ontario, the EV SUV and deal, open the payment calculator, fill in BIWEEKLY frequency and $5,000 down — LEASE at 48 months with 20,000 km/yr allowance, FINANCE at 72 months — then copy the FINAL address-bar URL per configuration. If the site encodes selections in the URL, that deep link is ideal; if not (SPA/page-state), share the deepest URL reached and briefly note which selections persisted in the URL vs page state. Never share homepages or unconfigured offer pages.

DELIVERY: Report to the schedule's configured delivery target (the SUV deal scan side chat) every morning.
DELIVERY HYGIENE (standing rule 2026-09-30, his correction): the deal alert carries ONLY the deal report — NO housekeeping footers, NO approval requests, NO task notes appended. Notes like "approved, go" belong in the goal's task tracker (timeline entries), never in the deal chat.

FORMAT: (1) DEAL REPORT collapsible panel on top — the chat markdown renderer does NOT collapse <details> blocks (verified 2026-09-24), so build it as an `html` widget via widget.create (kind "html", fallback_text "Deal report") and embed the returned token at the very top of the message, above the deals section. Theme-aware <details>/<summary> titled "Deal Report" (collapsed by default) with a two-column Setting|Value table. Rows: Region=Ontario; Down payment=$5,000; Payment frequency=Bi-weekly, taxes included; Lease config=48 months · 20,000 km/yr; Finance config=72 months; Lease target=≤$265 bi-weekly; Finance target=≤$365 bi-weekly; Vehicle scope=EV only — no PHEVs or hybrids; EVAP=$5,000 BEV (2026; ≤$50k transaction value), folded into payments; Loyalty rate=Kia only; Offer period=<current programs and end date>.
(2) DEALS section in markdown: one group header line per deal: **Deal:** <year> <make> <model> <trim> (<build code>, above base) · MSRP $X · Rebate −$Y (<name>) · Net $Z → $W (post-EVAP). Under each header a per-option table with exactly TWO columns: Option | Rate → bi-weekly payment — ONE ROW PER CONFIGURATION (lease 48 mo and finance 72 mo on separate rows, never columns). The Option cell is a short labeled link to that configuration's pre-configured page per the LINKS rule (e.g. [Lease 48 mo / 20k km](url)) — NO separate Status column, NO separate Link column. Bold the qualifying payment: that bolding alone marks qualification (no ✅/✗ status column). State the Kia loyalty reduction explicitly in the Rate cell when applied.
- Verdict line above the DEALS section: how many deals hit a target, or "no deal hit either payment target".
- If ≥1 deal hits a target: each qualifying deal as its own group header + option rows.
- If none hit: say so plainly, then the same group-row format (max 3 deals) for the cheapest near-misses — the lowest-payment deals found, bi-weekly payment up to a $400 MAX on any configuration, drawn from ALL EV manufacturers checked.
Keep it concise. Log the run outcome to the goal timeline via user_goal.create_entry on goal_e8a8f8022330.

SHEET-EDIT RULE (standing 2026-09-30): after posting the chat report, also update the shared EV payments Google Sheet — BalRam's one lookup sheet (link in the goal area). Edits go through the Sheets API only (never the browser). Update ONLY the data cells for today's date row — never move or reorder columns/rows, never touch headers. If the API call fails, note it in the timeline entry and move on — the chat report is the deliverable, the sheet is a convenience.
