# LinkedIn daily — 2026-08-27

## Status
**STOPPED** — LinkedIn login required. **0** confirmed applies (none invented).

## Login
- Preflight OK: resume `Rafi_Resume.docx` ready; LinkedIn `sourceHasAuth` / `destHasAuth` for `li_at` in SQLite
- Live CDP: stale session → `/uas/login` (exit 5); `CDP_REQUIRE_LIVE_LOGIN=1` refused continue
- Auto-login: Google SSO clicked → timed out; password candidates (2) → **Wrong email or password** (`wrong_password`, exit 5)
- `GOOGLE_PASSWORD` unset; Google cookie names present (`google_session: true`) but SSO did not complete
- Artifact: `/opt/cursor/artifacts/linkedin-auto-login-wrong-password.png`

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | login / wrong password |

## Code fix (this run)
None — owner secret / live-session blocker only (not code-fixable). Fourth consecutive cloud morning (2026-08-24…27) blocked the same way.

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** (and ideally **`GOOGLE_PASSWORD`**) — current LinkedIn password secret is rejected
2. If Security Verification / CAPTCHA appears after secret refresh: `bash scripts/home-headed-login.sh linkedin` then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LinkedIn daily after secrets+session are live

## False-skip suspects
None (no search/apply inventory processed).
