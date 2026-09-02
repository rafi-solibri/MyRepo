# LinkedIn daily — 2026-09-02

## Status
**STOPPED** — LinkedIn login required. **0** confirmed applies (none invented).

## Login
- Preflight: OK (`sourceHasAuth` / `destHasAuth` for `li_at`); resume `resumes/Rafi_Resume.docx` ready (20945B)
- Live CDP: dead session → `/login` (exit 5); SQLite `li_at` alone insufficient
- **Code fix (this run):** `challenge/pwd` was misclassified as Google 2FA → 300s `ASK_OWNER_GOOGLE_2FA` wait and skipped `GOOGLE_PASSWORD` fill. Fixed in `tools/google_2fa_prompt.py` + `_heal_google_auth_pages` (password heal before 2FA wait). Branch: `cursor/linkedin-fix-challenge-pwd-not-2fa-a239` (pushed).
- After fix re-login: `google_password_heal: wrong_password` (no fake 2FA wait) → LinkedIn password candidates (2) rejected → **Security Verification CAPTCHA** (exit 6) at `/checkpoint/challenge/…`
- Secrets present: `LINKEDIN_EMAIL`, `LINKEDIN_PASSWORD`, `GOOGLE_EMAIL`, `GOOGLE_PASSWORD`, `NAUKRI_WORKDAY_PASSWORD` — Google + LinkedIn passwords both rejected
- Artifacts: `/opt/cursor/artifacts/linkedin-auto-login-wrong-password.png`, `/opt/cursor/artifacts/linkedin-auto-login-captcha.png`

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | wrong password (Google + LinkedIn) → CAPTCHA checkpoint |

## Code fix (this run)
| Issue | Fix |
| --- | --- |
| Google `challenge/pwd` treated as 2FA; waited 300s; never filled `GOOGLE_PASSWORD` | Exclude `challenge/pwd` from `is_google_2fa_challenge`; heal password form before 2FA wait |

PR open/merge blocked this run: automation `CallDynamicTool` fails looking up `Cursor Automation Tools)` (trailing paren), and `gh pr create` returns 403 for the integration token. Branch is pushed for owner/merge once PR tooling works.

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** and **`GOOGLE_PASSWORD`** (both rejected)
2. Complete Security Verification / headed login: `bash scripts/home-headed-login.sh linkedin`, then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Open+merge PR from `cursor/linkedin-fix-challenge-pwd-not-2fa-a239` into `main`
4. Re-run LinkedIn daily after secrets+session are live

## False-skip suspects
None (no search/apply inventory processed).
