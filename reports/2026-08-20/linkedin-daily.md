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

## Post-fix re-run (same day, after PR #220)

**STOPPED — owner Google reCAPTCHA.** Resume-tailor code from the merged PR is on `main` and was loaded (`8a7f3e9`), but Easy Apply / external ATS never started. Did not invent applies.

- `POST_FIX_RERUN=1` on 2026-08-20 IST
- Preflight: resume + cookie sync OK (`sourceHasAuth` / `destHasAuth` true for `li_at`; `resumes/Rafi_Resume.docx`)
- CDP launch: WARP SOCKS `socks5://127.0.0.1:40000` + live probe → login required (SQLite `li_at` present but not live; redirected to `/uas/login`)
- Auto-login: Google SSO clicked (`google_session: true`) then password fallback → `/checkpoint/challenge` **Let’s do a quick security check** (Google reCAPTCHA “I’m not a robot”)
  - Kind: interactive CAPTCHA (`captcha_checkpoint`, auto-login exit **6**) — not the morning temporary-restriction page
  - Waited ~3.5 min on the wall; still on Security Verification; `li_at` absent after the attempt
  - `CDP_REQUIRE_LIVE_LOGIN=1` refused to continue without a live session
- Screenshot: `/opt/cursor/artifacts/checkpoint-page-0.png`
- Prompt rule: do not ask headed-login when CAPTCHA (6) **and** Google session is present — owner must complete the security check
- Resume tailor (`tools/resume_tailor.py`) was **not exercised** — no job pages reached
- Same-day post-fix re-run count for this portal: **1 / 5** (no further auto re-run; CAPTCHA is owner-only)
- Totals this re-run: Easy Apply **0**, external **0**, skipped **0**
- Status email: Resend id `bffb09eb-cb6f-4925-8f39-ee34935662a6` (testing sender `Job Status <onboarding@resend.dev>`; `RESEND_FROM_EMAIL` unset / no verified domain)
- No auto-fix PR from this re-run (CAPTCHA / login walls are owner-only per `automation-prompts/AUTO_FIX.md`)
