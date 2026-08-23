# LinkedIn daily — 2026-08-24 (post-fix re-run)

## Status
**STOPPED — login wall (owner-only).** Preflight + Chrome CDP + auto-login ran on merged `main` (`8b29a84` / PR #245 resume refresh). **0 confirmed applies.** Did not invent applies.

This is the same-day post-fix re-run after https://github.com/rafi-solibri/MyRepo/pull/245. The earlier run merged the resume refresh and handed off; this job used that code.

## Totals
- Easy Apply submitted: **0**
- External / ATS completed: **0**
- Skipped: **0** (helpers never started — no live session)
- Blocked: entire run (stale `li_at` + rejected password secrets)

## Login
- Preflight OK: resume `resumes/Rafi_Resume.docx` (merged master, 12516 bytes) + cookie sync (`sourceHasAuth` / `destHasAuth` true for `li_at`)
- CDP: WARP SOCKS `127.0.0.1:40000` + Chrome 148
- Live probe: SQLite `li_at` present but session dead → `/uas/login` (`linkedin_login_required`)
- Auto-login: Google cookie *names* present (`SID` / `__Secure-1PSID`) but GSI opened a **fresh Google identifier** form (stale Google session). Chrome log: `OnGetTokenFailure: Invalid credentials`
- Welcome-back card: Rafi Ahmed Mohammed Abdul / `r*****@gmail.com`
- `LINKEDIN_PASSWORD`: LinkedIn UI **That's not the right password.**
- Same secret on Google identifier: **Wrong password**
- `NAUKRI_WORKDAY_PASSWORD` (distinct candidate): also **That's not the right password.** on LinkedIn
- Not CAPTCHA (exit 6) and not a temporary restriction (exit 7)

## Submitted
- (none)

## Skipped
- (none — Easy Apply / external helpers not started)

## Blocked
- Entire run: owner must update Cursor secret `LINKEDIN_PASSWORD` (and optionally `GOOGLE_PASSWORD`) **or** headed-login:
  - `bash scripts/home-headed-login.sh linkedin`
  - `bash scripts/refresh-portal-session-seed.sh linkedin`
  - Save the cloud environment snapshot

## Code fix (this session)
- Helper was reporting generic timeout / `linkedin_login_required` while the page said wrong password, and GSI identifier/password was not filled when Google cookies were stale.
- Durable: detect wrong-password copy; try unique secret aliases; per-method wait; complete Google identifier form; screenshot `linkedin-auto-login-wrong-password.png`
- Issues log: `automation-prompts/issues/linkedin.md`

## Artifacts
- `/opt/cursor/artifacts/linkedin-login-now.png` (Welcome back)
- `/opt/cursor/artifacts/linkedin-gsi-popup.png` (Google identifier)
- `/opt/cursor/artifacts/apply-report.json`

## Same-day re-run cap
- This job is post-fix re-run #1 for LinkedIn on 2026-08-24 IST (`POST_FIX_RERUN=1`). Cap is 5. A further re-run will still fail until the password/session is refreshed.
