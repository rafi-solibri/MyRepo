# LinkedIn daily — 2026-08-26

## Status
**STOPPED** — LinkedIn login required. **0** confirmed applies (none invented).

## Login
- Preflight: OK — `sourceHasAuth` / `destHasAuth` for LinkedIn; resume `Rafi_Resume.docx` ready (rebuilt from master)
- Live CDP: stale `li_at` → `/uas/login` (exit 5)
- Auto-login: Google SSO clicked → timed out; password candidates (2) → **Wrong email or password** (`wrong_password`)
- `GOOGLE_PASSWORD` unset; `google_session` cookie names present but SSO did not complete
- Artifact: `/opt/cursor/artifacts/linkedin-auto-login-wrong-password.png` (also `reports/2026-08-26/linkedin-auto-login-wrong-password.png`)

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | login / wrong password |

## Code fix (this run)
None — owner secret / live session blocker (not code-fixable per AUTO_FIX). Helper already detects wrong password and tries Google SSO + password aliases.

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** (and ideally **`GOOGLE_PASSWORD`**) — current LinkedIn password secret is rejected
2. If Security Verification / CAPTCHA appears after secret refresh: `bash scripts/home-headed-login.sh linkedin` then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LinkedIn daily after secrets+session are live

## False-skip suspects
None (no search/apply inventory processed).
