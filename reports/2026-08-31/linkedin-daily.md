# LI daily — 2026-08-31 (POST_FIX_RERUN)

## Status
**STOPPED** — portal login required. **0** confirmed applies (none invented).

This is the same-day post-fix re-run (`POST_FIX_RERUN=1`) on `main` @ `688ff71` (`#298` plus earlier `#293` pacing/tailor). The morning cron (`bc-17d06ef9-13c8-4e72-8309-ef7247f13e3f`) also recorded **0** applies and did **not** apply with a live session.

## Login
- Preflight: OK (`sourceHasAuth` / `destHasAuth`); resume `Rafi_Resume.docx` ready (20945B, rebuilt from master)
- Chrome CDP + WARP SOCKS: ready
- Live CDP: SQLite `li_at` **name** present but session dead → `/uas/login` (exit 5)
- Auto-login: Google SSO clicked → late `challenge/pwd` healed → **Wrong password** (`google_password_heal`); portal password candidates **(2)** → **Wrong email or password**
- After rejected secrets: `/checkpoint/challenge` **Security Verification** / reCAPTCHA (auto_login exit **6**, `reason=captcha_checkpoint` while `wrong_password=true`)
- Secrets present (portal password env len=9; Google password env aliased to the same value) — both rejected
- Ninth consecutive calendar morning (24–31) blocked on rejected password secrets
- Artifacts: `/opt/cursor/artifacts/li-auto-login-wrong-password.png`, `/opt/cursor/artifacts/li-auto-login-captcha.png`

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a (no search/apply inventory processed) |
| Blocked | login / wrong password (Google + portal), then CAPTCHA after retries |

## Code fix (this run)
None — same owner-secret blocker as the morning run (AUTO_FIX.md: login walls / CAPTCHA / OTP are owner-only). Helper already detects `wrong_password` and heals late Google password during SSO wait. Precedence quirk (exit 6 captcha after wrong-password retries) does **not** unblock applies; not launching another post-fix re-run for it (slot 1/5 used by this job).

Merged PR referenced by the launcher: https://github.com/rafi-solibri/MyRepo/pull/298 (hitechcity; already on `main`). LI durable helpers from `#293` were already on `main` for this re-run.

## Owner action (required before applies)
1. Update Cursor secrets for the portal password and Google password — both rejected
2. After secrets are corrected: if Security Verification / CAPTCHA / authenticator appears, complete headed login / phone 2FA (`ASK_OWNER_GOOGLE_2FA (li)`), then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LI daily after secrets+session are live — do **not** ask headed-login until CAPTCHA after secrets are corrected

## False-skip suspects
None (no search/apply inventory processed).
