# LinkedIn daily — 2026-08-29 (POST_FIX_RERUN #2)

## Status
**STOPPED** — LinkedIn login required. **0** confirmed applies (none invented).

Ran on merged `main` `d996c63` (PR #286). Preflight + Chrome CDP + auto-login executed. Apply helpers were not started because live session never opened.

## Login
- Preflight: OK (`sourceHasAuth` / `destHasAuth` `li_at` cookie names)
- Live CDP: stale `li_at` → `/uas/login` then `/login` (exit 5)
- Auto-login (merged heal from #283): Google SSO clicked → late `challenge/pwd` healed → **Wrong password** (`google_password_heal`)
- LinkedIn password form: **Wrong email or password** (screenshot)
- Candidates tried: `LINKEDIN_PASSWORD` + `NAUKRI_WORKDAY_PASSWORD` (2 unique). `GOOGLE_PASSWORD` is **not** in this environment’s secrets — `load-job-secrets.sh` aliases it from `LINKEDIN_PASSWORD`
- No CAPTCHA / Security Verification this re-run (unlike first post-fix re-run)
- Artifact: `/opt/cursor/artifacts/linkedin-auto-login-wrong-password.png`

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | login / wrong password (Google + LinkedIn) |

## Code fix
None this re-run. Earlier same-day code fix (#283 Google SSO heal) is already on `main` and **did run**. Remaining blocker is owner secrets / live session — not code-fixable. Did **not** launch another post-fix re-run (would loop on the same rejected password). Cap used: 2 / 5.

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** and add a real **`GOOGLE_PASSWORD`** (do not reuse the rejected LinkedIn value)
2. If Security Verification / CAPTCHA / authenticator appears after secret refresh: complete headed login / phone 2FA, then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LinkedIn daily after secrets+session are live

## False-skip suspects
None (no search/apply inventory processed).
