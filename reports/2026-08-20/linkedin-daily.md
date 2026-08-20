# LinkedIn daily — 2026-08-20

## Status
**STOPPED — temporary account restriction (owner-only).** No applications submitted. Did not invent applies.

## Totals
- Easy Apply submitted: **0**
- External completed: **0**
- Skipped: **0** (helpers never started — no live session)
- Blocked: login wall / temporary restriction

## Login
- Preflight: resume + cookie sync OK (`sourceHasAuth` / `destHasAuth` true for `li_at`)
- CDP launch: WARP SOCKS + live probe → `linkedin_login_required` (SQLite `li_at` present but not live)
- Auto-login: Google SSO clicked → `/checkpoint/challenge` **account temporarily restricted**
  - Kind: `account_temporarily_restricted` (not interactive CAPTCHA)
  - `lift_utc`: **2026-08-23T03:30:00+00:00** (~72h from run start)
  - `seconds_until_lift`: ~259138
  - Default `LINKEDIN_RESTRICTION_WAIT_MAX_S=7200` — wait beyond budget → exit **7**
- `CDP_REQUIRE_LIVE_LOGIN=1` refused to continue without a live session
- Screenshot: `/opt/cursor/artifacts/linkedin-auto-login-captcha.png` (restriction page; filename legacy)

## Submitted
- (none)

## Skipped
- (none — search/apply helpers not run)

## Blocked
- Entire run: LinkedIn temporary restriction until **2026-08-23 03:30 UTC**
- Owner action: wait until lift, then re-run `bash scripts/preflight-portal-run.sh linkedin` + `bash scripts/launch-chrome-cdp.sh linkedin` (or next cron after lift). Interactive CAPTCHA not required unless it appears post-lift.

## Notes
- Same restriction pattern as 2026-08-19, but lift is multi-day (not same-day waitable)
- No code-fixable apply blocker; auto_login already distinguishes restriction vs CAPTCHA and waits within budget
