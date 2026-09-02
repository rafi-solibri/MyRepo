# Daily apply — 2026-09-02 (post-fix re-run)

## Status
**STOPPED** — login required. **0** confirmed applies (none invented).

## Login
- Preflight: OK (`sourceHasAuth` / `destHasAuth` for `li_at`); resume `resumes/Rafi_Resume.docx` ready (20945B)
- Live CDP: dead session → `/uas/login` (exit 5); SQLite `li_at` name alone insufficient
- Auto-login (local SSO fix, ~26s): Google SSO clicked → `challenge/pwd` classified as **password** (not 2FA; no 300s wait) → `google_password_heal: missing_google_password` → **skipped** portal-password fallback (no Security Verification CAPTCHA; exit 5 not 6)
- Secrets this run: portal email SET, portal password SET (len 9), **`GOOGLE_PASSWORD` UNSET**, `GMAIL_APP_PASSWORD` UNSET
- `google_session: true`; `google_password_candidates: 0`; `password_candidates: 2` (not used after missing Google password)
- Artifact: `/opt/cursor/artifacts/auto-login-missing-google-password.png` (Google identifier form after SSO)
- Did **not** ask headed-login (Google session present + missing `GOOGLE_PASSWORD` — owner must set the Gmail secret first)

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | missing `GOOGLE_PASSWORD` after Google SSO password challenge |

## Code fix (this run)
| Issue | Fix |
| --- | --- |
| Google `challenge/pwd` treated as 2FA (300s wait); `load-job-secrets.sh` aliased the portal password into `GOOGLE_PASSWORD`, then portal-password fallback burned CAPTCHA | Classify `challenge/pwd` as password; one-way alias only; skip portal-password fallback when `GOOGLE_PASSWORD` is missing |

Fix commit: `14f369b` (pushed on this re-run branch).
`gh pr create` / REST API: **403** Resource not accessible by integration. ManagePullRequest registered for owner approval.

Did **not** launch another same-day post-fix re-run: remaining blocker is an owner secret (`GOOGLE_PASSWORD` unset), not a new code bug. Re-run count for this portal today: 2 / 5.

## Owner action (required before applies)
1. Set Cursor secret **`GOOGLE_PASSWORD`** (Gmail account password — do not reuse the portal password)
2. Refresh the portal password secret if it is still the rejected 9-character value
3. If Security Verification / CAPTCHA / authenticator appears after secret refresh: complete headed login / phone 2FA (`ASK_OWNER_GOOGLE_2FA`), then seed refresh / push `.portal-sessions` Cookies (omit Local State)
4. Merge the SSO fix (`14f369b`) into `main` (PR tooling 403 from this agent)
5. Re-run the daily job after secrets+session are live

## False-skip suspects
None (no search/apply inventory processed).
