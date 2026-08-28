# Daily report — 2026-08-28 (post-fix re-run)

## Status
**STOPPED** — login required. **0** confirmed applies (none invented).

POST_FIX_RERUN=1 after merged **#282** (Hirist Gmail Passwd fill + session). Checked out `origin/main` at `5a71a82` before preflight. Morning cron (`bc-cdcb72f6-ab84-4a06-a8f7-279b7ec3b915`, draft **#276**) also applied **0** (stale `li_at` + `wrong_password`).

## Login
- Preflight OK: `Rafi_Resume.docx` rebuilt from master; cookie **names** `sourceHasAuth` / `destHasAuth` true
- Live CDP: stale `li_at` → `/uas/login` (wait_for_cdp_login exit 5)
- Auto-login: Continue with Google reached **`/signin/challenge/pwd`**. First attempt treated that URL as 2FA and **timed out** (same gap Hirist #282 fixed)
- After helper patch: Passwd field **is filled**; Google returns **Wrong password. Try again** for both unique secrets (9-char portal password aliased as `GOOGLE_PASSWORD`, and 18-char Workday password)
- Native portal password on `/login` also `wrong_password` (2 candidates)
- `google_session` cookie names present but session is dead; Hirist-profile Google cookie copy did not skip the password page
- Artifacts: `/opt/cursor/artifacts/linkedin-google-challenge-pwd.png`, `linkedin-auto-login-wrong-password.png` <!-- pragma: allowlist secret -->

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | login / Google + portal `wrong_password` |

## Code fix (this run)
- Fill `input[name=Passwd]` after GSI account chooser; `google_2fa_prompt` excludes `/signin/challenge/pwd` from 2FA wait
- `sys.path` insert so `from tools.google_2fa_prompt` works when the helper is run as a script
- Issues: `automation-prompts/issues/linkedin.md` <!-- pragma: allowlist secret -->
- Tests: `python3 tools/test_google_2fa_prompt.py`, `pytest tools/linkedin/test_auto_login_restriction.py` <!-- pragma: allowlist secret -->

This does **not** unblock today’s applies: Google still rejects the stored password secrets.

## Owner action (required before applies)
1. Set Cursor secret **`GOOGLE_PASSWORD`** to the real Gmail account password (do not alias the 9-char portal secret)
2. Refresh the native portal password secret if `/login` should work as fallback
3. If Security Verification / CAPTCHA appears: `bash scripts/home-headed-login.sh linkedin` then seed refresh / push `.portal-sessions` Cookies (omit Local State) <!-- pragma: allowlist secret -->
4. Re-run the daily job after secrets + live session

## False-skip suspects
None (no search/apply inventory processed).
