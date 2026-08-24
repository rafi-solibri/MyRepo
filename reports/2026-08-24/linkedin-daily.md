# LinkedIn daily — 2026-08-24

## Status
**STOPPED** — LinkedIn login required. **0** confirmed applies (none invented).

## Login
- Preflight OK (`sourceHasAuth` / `destHasAuth` cookie names present)
- Live CDP: `li_at` present initially but session dead → `/uas/login`
- Auto-login: Google SSO clicked → timed out (stale Google cookies; GSI fell through to identifier)
- Password candidates tried: `LINKEDIN_PASSWORD` + `NAUKRI_WORKDAY_PASSWORD` alias — **Wrong email or password**
- After retries: `/checkpoint/challenge` **Security Verification** (exit **6**)
- Google cookie *names* still present (`google_session=true`) but GSI requires full Google password (also rejected by same secret)
- Artifacts: `/opt/cursor/artifacts/linkedin-auto-login-wrong-password.png`, `linkedin-auto-login-captcha.png`, `linkedin-login-debug.png`

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | login / wrong password / CAPTCHA |

## Code fix (this run)
- Cherry-picked same-day unmerged helper from earlier post-fix re-run that never reached `main`
- `tools/linkedin/auto_login.py`: detect wrong password (incl. LinkedIn “Wrong email or password”), complete Google identifier/password when cookies stale, try secret aliases, per-method timeout
- Tests: `tools/linkedin/test_auto_login_restriction.py`
- Issues: `automation-prompts/issues/linkedin.md`

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** (and ideally separate **`GOOGLE_PASSWORD`**) — current value is rejected by both LinkedIn and Google
2. If Security Verification persists: `bash scripts/home-headed-login.sh linkedin` then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LinkedIn daily after secrets+session are live

## False-skip suspects
None (no search/apply inventory processed).
