# Portal — Site Architecture

**Created:** September 27, 2026 · **Last updated:** September 27, 2026
**Live at:** https://portal.technology-consults.workers.dev

## 1. What this is

A private front door for BalRam's trackers, documents, and files. Nothing here is public: every page except the sign-in screen requires a logged-in session. It replaces the old public GitHub Pages hosting, which was shut off on September 27, 2026.

## 2. The three moving parts

| Part | What it is | Plain-words role |
|---|---|---|
| Cloudflare Worker | A small server program (file: `src/worker.mjs`) | The doorman: checks logins, keeps sessions, serves pages only to signed-in users |
| Cloudflare KV (`portal-kv`) | A key-value store (like a big labelled locker) | Where every page, file, user record, code, and session lives |
| Resend | An email-sending service | Mails the one-time login codes |

There is no traditional web server and no database. The Worker is the entire backend; KV is the entire storage.

## 3. Pages and routes

| Address | Who can see it | What it does |
|---|---|---|
| `/` | Anyone | Sign-in screen: enter username, get a code by email. No password exists anywhere in the system. |
| `/api/login` | Anyone (rate-limited) | Step 1: checks the username, stores a 6-digit code, emails it |
| `/api/verify` | Anyone (rate-limited) | Step 2: checks the code, creates the session |
| `/portal` | Signed-in users | Hub: cards for the status tracker and artifacts, profile/session info, logout |
| `/api/me` | Signed-in users | Returns who you are, your role, login timestamps (used by the hub) |
| `/api/logout` | Signed-in users | Ends the session |
| `/p/...` | Signed-in users | All private content: the status board, artifact files, documents |

Anonymous visitors to `/p/...` are bounced back to the sign-in screen (or get a 401 for background requests). There is no way to guess a URL and read private content.

## 4. How sign-in works (passwordless)

1. You type your username and tap **Send code**.
2. The Worker looks up `user:<username>` in KV. Unknown names get a flat "auth failed" — the system never says whether a name exists.
3. It creates a random 6-digit code, stores it under `code:<username>` (expires in 10 minutes), and emails it via Resend.
4. You type the code. The Worker compares it, deletes it immediately (single use — a code can never work twice), and creates a session.
5. The session is a random token in a cookie (`__portal_sess`). The cookie is `HttpOnly` (page scripts can't read it), `Secure` (https only), and `SameSite=Lax`.

Wrong guesses are counted: 5 wrong tries on one code destroys it. Login attempts are throttled at 8 per internet address per 10 minutes.

## 5. Sessions and the 15-minute timeout

| Rule | Detail |
|---|---|
| Lifetime | 15 minutes of inactivity, then you're signed out |
| Sliding | Every request pushes the expiry another 15 minutes |
| Browser watchdog | Each private page runs `_sess.js`, which checks the session every 60 seconds and redirects to sign-in the moment it dies |
| Storage | `sess:<token>` in KV, holding username, role, and login time |

The hub's profile view shows username, email, role, "logged in since", and previous login time (from `umeta:<username>` — codes and secrets are never stored there).

## 6. What lives in KV (key layout)

| Key pattern | Content |
|---|---|
| `pub:login.html`, `pub:hub.html` | The public sign-in page and the hub page |
| `p:board`, `p:tasks.json` | The status tracker page and its data |
| `p:<path>` | Every artifact file and document (50+ keys) |
| `p:_sess.js` | The inactivity watchdog, auto-attached to every HTML page |
| `user:<username>` | User record: email, role (`admin` = read-write, regular = read-only) |
| `code:<username>` | Pending login code (10-minute life, max 5 guesses) |
| `sess:<token>` | Active session (15-minute sliding life) |
| `umeta:<username>` | Login history: last and previous login timestamps |
| `rl:<ip>` | Rate-limit counters |

Two accounts exist: `balram.bandhu.admin` (admin) and `balram.bandhu` (regular, currently parked — Resend's test mode can't email it yet).

## 7. How content gets published

The portal never reads from GitHub. Publishing is a push: local scripts upload to the repo **and** to the portal's KV.

| Content | Script | Destination |
|---|---|---|
| Status tracker | `board-build/push_board.py` | GitHub repo + KV (`p:board`, `p:tasks.json`) |
| Artifact files | `push_content.py` (KV) + API upload (repo) | GitHub repo `muse-artifacts/` + KV (`p:<path>`) |
| Portal code/pages | Cloudflare API deploy | KV (`pub:*`, `p:_sess.js`) + Worker script |

Per current instruction, changes are batched locally and deployed together on BalRam's word — not one-by-one.

## 8. Email delivery

Login codes are sent through Resend's API from the Worker, currently from `Portal login <onboarding@resend.dev>`. The account is in test mode with no verified domain, so mail can only reach `technology.consults@gmail.com` — this is why the regular user is parked.

**Known incident (2026-09-27):** from ~5:47 PM EDT, the Worker's calls to Resend began failing while direct API calls with the same key kept working. Leading diagnosis: Resend throttling Cloudflare Workers' shared outbound addresses. The login pattern itself (emailed one-time codes) is standard; the weak point is sending from a free shared-IP tier with no retry and a swallowed error message. Fix planned: automatic retry with backoff and surfacing the real error.

## 9. Security controls in place

| Control | Setting |
|---|---|
| Passwords | None exist — passwordless only, per explicit requirement |
| Code life | 10 minutes, single use, 5 wrong guesses destroys it |
| Login throttling | 8 attempts per IP per 10 minutes |
| Session | 15-minute sliding inactivity timeout, server + browser enforced |
| Cookie | HttpOnly, Secure, SameSite=Lax |
| Username probing | Unknown names get the same flat error as wrong codes |
| Content protection | Every `/p/...` request re-checks the session |

## 10. Open gaps (not yet done)

| Gap | Status |
|---|---|
| Code randomness uses `Math.random()`, not cryptographic randomness | To fix |
| No unique ID binding a code to one login attempt | To fix |
| No durable audit trail (login/mail/verify/session events) | To fix |
| No formal end-to-end production auth test (logout, code reuse, idle expiry) | To fix |
| KV values capped at 25 MB vs the 100 MB artifact rule | To resolve |
| GitHub repo may still be publicly readable (Pages is dead, repo visibility unchecked) | To verify |
| Portal source not yet in a GitHub repo | To do |
| Timestamps: pages show "Page updated" but not separate created/last-modified | To add |

## 11. Costs

Cloudflare Workers free tier + KV free tier + Resend test mode: $0/month at current usage.
