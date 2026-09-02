# Google / Gmail auth (all portals)

Use this on **every** LinkedIn, Foundit, Naukri, Cutshort, Instahyre, Indeed, Hirist, and Hitech City run.

## Rules (HARD)

1. **Prefer Gmail / Continue with Google** when the portal offers Google SSO (LinkedIn, Hirist, etc.). Account: Cursor secret `GOOGLE_EMAIL` / `LINKEDIN_EMAIL` (default owner Gmail).
2. **Email verification / OTP** from Google or ATS (Oracle, Greenhouse, etc.): autofill via `tools/ats/email_otp.py` (Gmail in the same Chrome CDP profile, or IMAP when `GMAIL_APP_PASSWORD` is set). Do **not** treat mailbox-readable email OTP as owner-only.
3. **Google 2-factor / authenticator / phone prompt:** print a loud `ASK_OWNER_GOOGLE_2FA (<portal>)` banner in the **agent chat** every time so the owner can see it on mobile and enter the code in Chrome (or tap Yes on the phone). Wait with `tools/google_2fa_prompt.py` (`GOOGLE_2FA_WAIT_SEC` default 300). Keep the challenge tab focused. Never invent codes.
4. Passwords: `GOOGLE_PASSWORD` and/or `LINKEDIN_PASSWORD` secrets. Wrong password → stop and report (owner updates secrets).
5. CAPTCHA remains owner-only (refocus tab); after solve, continue applying.

## Helpers

| Portal | Helper |
| --- | --- |
| LinkedIn | `tools/linkedin/auto_login.py` (Google SSO + 2FA chat wait) |
| Hirist | `node tools/hirist/google_login.js` then `daily_apply.js` |
| Indeed | `tools/indeed/google_sso.py` (wired from `uc_daily_apply` on Sign-in wall; `GOOGLE_PASSWORD` only) |
| ATS email OTP | `tools/ats/email_otp.py` |
| Shared 2FA banner | `tools/google_2fa_prompt.py` (`/challenge/pwd` is password, not 2FA) |

**HARD:** set `GOOGLE_PASSWORD` (Gmail) separately from `LINKEDIN_PASSWORD`. Never cross-feed.
