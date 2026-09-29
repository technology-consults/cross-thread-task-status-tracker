---
id: portal-links-watch
title: Portal links registry watch
enabled: true
mode: task
schedule:
  kind: daily
  timezone: '@user.current'
  time: 07:42:00
timeout_secs: 300
delivery:
  - chat_id: d8dbccdb-6bd0-4b1a-8f63-1e80592412d4
metadata:
  tags: [cron:flexible-time]
  originating_chat_context_json: '{"chat_id":"d8dbccdb-6bd0-4b1a-8f63-1e80592412d4","origin_provider":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
You are the portal-links registry watcher. Once per run, verify every URL in the standing portal registry against the last registry posted in this chat (the "Portal links" side chat) and post here ONLY if something changed.

URLs to check (fetch each, record HTTP status + basic content sanity):
1. https://portal.technology-consults.workers.dev/ — Portal hub (expect 200)
2. https://portal.technology-consults.workers.dev/p/board — Status tracker (expect 200)
3. https://portal.technology-consults.workers.dev/p/artifacts/ — Artifacts index (expect 200)
4. https://portal.technology-consults.workers.dev/p/ev-deals/ — EV deals page (expect 200)
5. https://technology-consults.github.io/trading-portal/etf-live.html — ETF live dashboard (expect 200; page title should mention QQQ/SPY/GLD)
6. https://portal.technology-consults.workers.dev/login — sign-in page (expect 200; currently dormant — the page should say sign-in is turned off)

Also spot-check the portal hub page for any new /p/ links that are not in the registry yet.

Compare against the most recent full registry table in this chat:
- If everything matches (same URLs, same live/dormant statuses): stay silent. End your run with exactly "Portal links: no changes."
- If anything changed (URL added, removed, killed, moved, or flipped live<->dormant): post the fresh FULL list here as a new message in this exact format: a line "---", then bold "Portal links — every URL, with status", then "Updated YYYY-MM-DD.", then a markdown table with columns URL | What it is | Status, then the rule paragraph in italics (not bold — the Muse app does not render <small>, so italics is the lightest available) exactly like this: *Rule for this thread: whenever a portal URL is added, changed, or removed, I post the fresh full list here. Live and dormant links appear every time. Killed links appear only in the one message right after they are killed, never again.*, then "---". Live and dormant links appear every time; a link killed since the last registry appears once as killed in this message and is omitted from all later ones. Verify every status live before posting — never restate a status from memory.

Do not post when nothing changed. Do not edit MEMORY.md; write notable observations to ~/memory/YYYY-MM-DD.md.
