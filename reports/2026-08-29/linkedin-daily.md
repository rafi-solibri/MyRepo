# LinkedIn daily — 2026-08-29

## Status
**STOPPED** — LinkedIn login required. **0** confirmed applies (none invented).

## Login
- Preflight: OK (`sourceHasAuth` / `destHasAuth`); resume `Rafi_Resume.docx` ready
- Live CDP: stale/missing `li_at` → `/uas/login` then `/login` (exit 5)
- Auto-login: Google SSO clicked → late `challenge/pwd` healed → **Wrong password** (`google_password_heal`); LinkedIn password candidates (2) → **Wrong email or password**
- `GOOGLE_PASSWORD` is set this run (unlike mornings 24–28) but **rejected** along with `LINKEDIN_PASSWORD`
- Artifact: `/opt/cursor/artifacts/linkedin-auto-login-wrong-password.png`

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | login / wrong password (Google + LinkedIn) |

## Code fix (this run)
- `tools/linkedin/auto_login.py`: heal Google identifier/password/2FA during `google_sso` wait and after account-chooser click (`_heal_google_auth_pages`); SSO no longer silent-timeouts while a late password form is open
- Tests: `tools/linkedin/test_auto_login_restriction.py`
- Issues: `automation-prompts/issues/linkedin.md`

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** and **`GOOGLE_PASSWORD`** — both candidates were rejected by Google and LinkedIn this morning
2. If Security Verification / CAPTCHA / authenticator appears after secret refresh: complete headed login / phone 2FA, then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LinkedIn daily after secrets+session are live

## False-skip suspects
None (no search/apply inventory processed).
