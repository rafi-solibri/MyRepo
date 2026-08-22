# LinkedIn daily — 2026-08-22

## Status
**STOPPED — temporary account restriction (owner-only).** No applications submitted. Did not invent applies.

## Totals
- Easy Apply submitted: **0**
- External completed: **0**
- Skipped: **0** (helpers never started — no live session)
- Blocked: login wall / temporary restriction

## Login
- Preflight: `bash scripts/preflight-portal-run.sh linkedin` OK — resume ready (`resumes/Rafi_Resume.docx`), cookie sync `sourceHasAuth` / `destHasAuth` true for `li_at`
- CDP: `bash scripts/launch-chrome-cdp.sh linkedin` — WARP SOCKS + live probe → `linkedin_login_required` (SQLite `li_at` present but not live)
- Auto-login: Google SSO clicked → `/checkpoint/challenge` **account temporarily restricted**
  - Kind: `account_temporarily_restricted` (not interactive CAPTCHA)
  - Page text: restriction lifted **August 22, 2026 8:30 PM PDT**
  - `lift_utc`: **2026-08-23T03:30:00+00:00**
  - `seconds_until_lift`: ~86344 (~24h)
  - Default `LINKEDIN_RESTRICTION_WAIT_MAX_S=7200` — wait beyond budget → exit **7**
- Google session: present (`google_session: true`) — do not ask headed-login (CAPTCHA exit 6 only when no Google session)
- `CDP_REQUIRE_LIVE_LOGIN=1` refused apply helpers
- Screenshot: `/opt/cursor/artifacts/linkedin-auto-login-captcha.png` (restriction page; filename legacy)

## Submitted
- (none)

## Skipped
- (none — search/apply helpers not run)

## Blocked
- Entire run: LinkedIn temporary restriction until **2026-08-23 03:30 UTC** (Aug 22 8:30 PM PDT)
- Next cron after lift should resume Easy Apply + external pass with `Rafi_Resume.docx` + per-job tailor

## False-skip suspects
- (n/a — no inventory scanned)
