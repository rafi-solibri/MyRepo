# LinkedIn daily — 2026-08-28

## Status
**STOPPED** — LinkedIn login required. **0** confirmed applies (none invented).

## Login
- Preflight OK: resume `Rafi_Resume.docx` ready; LinkedIn `sourceHasAuth` / `destHasAuth` for `li_at`
- Live CDP: stale session → `/uas/login` (exit 5)
- Auto-login: Google SSO clicked → timed out; password candidates (2) → **Wrong email or password** (`wrong_password`, exit 5)
- `GOOGLE_PASSWORD` unset; Google cookie names present but SSO did not complete
- Artifact: `/opt/cursor/artifacts/linkedin-auto-login-wrong-password.png`
- Fifth consecutive morning (24–28) same owner-secret blocker

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | login / wrong password |

## Code fix (this run)
None — owner secret blocker (not code-fixable). Login walls / wrong password are owner-only per prompt.

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** (and ideally **`GOOGLE_PASSWORD`**) — current LinkedIn password secret is rejected
2. If Security Verification / CAPTCHA appears after secret refresh: `bash scripts/home-headed-login.sh linkedin` then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LinkedIn daily after secrets+session are live

## False-skip suspects
None (no search/apply inventory processed).
