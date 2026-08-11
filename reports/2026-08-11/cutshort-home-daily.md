# Cutshort home daily 2026-08-11

**STOP: Cutshort login/session missing (stale CDP cookie + Cloudflare Turnstile).**

- Preflight: SQLite `destHasAuth: true` but live CDP redirects to `/?redirect_url=%2Fprofile%2Fcandidate-dashboard`
- Cloudflare Turnstile iframe present on the landing page (`failure_retry`)
- Applied: **0** | Seen: **0** | Blocked: **1**
- JSON: `artifacts/cutshort-daily-run.json` → `automation-results/cutshort/2026-08-11.json`

## Owner action (required)
1. In the headed Chrome CDP window (profile `~/.cursor/chrome-cdp-profiles/cutshort`), complete any Turnstile checkbox.
2. Sign in at https://cutshort.io/login (rafi.success@gmail.com).
3. Confirm candidate dashboard loads, then reply here (or re-run):
   `bash scripts/portal-home-daily.sh cutshort`
   or `node tools/cutshort/daily_apply.js`

Helper: `bash scripts/home-headed-login.sh cutshort`

## Code shipped this run
- PR #70: `tools/cutshort/wait_for_cdp_login.js` + home-headed-login wiring
- PR #71: waiter race harden (settle redirect + require dashboard body signals)
