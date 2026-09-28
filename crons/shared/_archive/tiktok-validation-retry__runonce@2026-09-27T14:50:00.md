---
id: tiktok-validation-retry
title: TikTok validation retry
enabled: true
owner: goal:short-video-creation-and-publishing-pipeline
mode: task
schedule:
  kind: runonce
  timezone: America/Toronto
  at: 2026-09-27T14:50:00
timeout_secs: 1800
metadata:
  originating_channel_context_json: '{"originating_channel":"main","chat_kind":"direct","event_kind":"message","require_mention":false,"device_id":"5cd90c63bc608a44"}'
  presentation_locale: en-US
---
One-time retry of the TikTok sign-in validation for the user's brand account.

Background (from 2026-09-27 ~1:40 PM EDT): the saved TikTok username/password from the Secure Vault were accepted by TikTok (no wrong-password error), but TikTok required an extra email-verification step to i***b@gmail.com (the brand email intelligently.artificial.collab@gmail.com). The verification code fetched from Gmail was entered once and rejected, after which TikTok rate-limited with "Maximum number of attempts reached. Try again later." Note: the user's TikTok 2FA was already disabled, so this was TikTok's own login-risk verification, not 2FA — only time clears the rate limit. Do not attempt repeated logins.

User's standing preference for TikTok: ALWAYS use TikTok's email-based login (log in with email + verification code sent to the account email), never the username/password form. When a code is needed, always fetch the LATEST TikTok verification code from Gmail (the user authorized reading his Gmail via the saved Google login in the Secure Vault for this purpose).

Steps:
1. Check the TikTok browser task state via browser.list_tasks; steer the existing task if usable, otherwise spawn a fresh browser task for the tiktok.com validation. (The earlier task browser-task:d90d0618-a03d-4f4e-80eb-3a39c7bc9857 was closed at the user's request around 1:45 PM EDT — check current state first.)
2. Make ONE careful attempt: dismiss any stale dialog, go to the TikTok login screen, and use the email login method (Continue with email, then log in with verification code). Send a FRESH code to the account email. Do NOT use the username/password login form.
3. If TikTok still shows "Maximum number of attempts reached" or any rate-limit message, STOP immediately and report that the cooldown is still in effect — do not keep retrying.
4. If no verification is requested and sign-in completes directly, report the signed-in username/handle as validated.
5. Otherwise, spawn a Gmail reader browser task: sign into https://mail.google.com/ with the saved Google login via the credential-fill flow, find the NEWEST TikTok verification-code email (received within the last 15 minutes), waiting and refreshing up to 3 minutes if needed. Relay the code ONCE into the TikTok task's code-entry step for this active challenge. Never repeat the code in the chat reply.
6. Report the final result in the Main chat: whether TikTok sign-in completed (with the username/handle shown) or the exact blocker text.

Read-only validation only: no posts, likes, follows, comments, or settings changes on TikTok; no sending, archiving, deleting, or settings changes in Gmail. A code the user or Gmail reader supplies is relayed once for its current step only. One attempt total — if blocked, stop and report.
