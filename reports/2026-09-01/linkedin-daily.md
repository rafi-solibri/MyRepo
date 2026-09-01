# LinkedIn daily — 2026-09-01

## Status
**STOPPED** — post-fix re-run 1 ran on merged `#305` (`6c3961b`) and still produced **0** confirmed applies (none invented).

## Login (post-fix re-run, HEAD `6c3961b`)
- Preflight: OK (`sourceHasAuth` / `destHasAuth` for `li_at`); resume `resumes/Rafi_Resume.docx` ready (20945B, rebuilt from master)
- Live CDP: stale `li_at` → `/uas/login` (exit 5)
- Auto-login (merged routing): Google SSO clicked → **`/v3/signin/challenge/pwd`** (password form)
- **New blocker:** `is_google_2fa_challenge` treated `/challenge/pwd` as 2FA (`ASK_OWNER_GOOGLE_2FA`) and waited 300s. Password heal never ran.
- `GOOGLE_PASSWORD` is **unset** in Cloud secrets. `scripts/load-job-secrets.sh` still aliased `LINKEDIN_PASSWORD` → `GOOGLE_PASSWORD` at launch (undoing `#305` isolation).
- After 2FA timeout: LinkedIn password candidate 1/2 → **Security Verification / reCAPTCHA** (exit 6)
- Artifact: `/opt/cursor/artifacts/linkedin-auto-login-captcha.png`
- Chrome tab: `linkedin.com/checkpoint/challenge` + `recaptcha/enterprise`

## Morning run (before this re-run)
- Stopped `wrong_password`; `GOOGLE_PASSWORD` unset; `#305` merged after that run so applies never used the fix.

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | Google pwd-as-2FA + LinkedIn CAPTCHA |

## Code fix (this re-run)
1. `tools/google_2fa_prompt.py` — `/challenge/pwd` and identifier are **not** 2FA
2. `tools/linkedin/auto_login.py` — heal **password first**, then real 2FA; identifier URL no longer matches all `/signin/challenge`
3. `scripts/load-job-secrets.sh` — **do not** copy `LINKEDIN_PASSWORD` → `GOOGLE_PASSWORD`

## Owner action (still required for applies)
1. Set Cursor secret **`GOOGLE_PASSWORD`** (Gmail) separately from **`LINKEDIN_PASSWORD`**
2. Complete headed login / Security Verification CAPTCHA if it persists: `bash scripts/home-headed-login.sh linkedin`
3. After secrets + live session, re-run LinkedIn daily

## False-skip suspects
None (no search/apply inventory processed).
