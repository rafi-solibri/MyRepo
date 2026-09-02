# Indeed daily — 2026-09-02 (post-fix re-run after #314)

## Status
**STOPPED** — Indeed login required. **0** confirmed applies (none invented).

Ran on merged `#314` (`17dc9fc`) first, then in-session helper fixes on
`cursor/indeed-daily-post-fix-re-run-2026-09-02-8146`.

## Login
- WARP+UC preflight **OK** (Turnstile cleared; HTTP/Chrome still 403 without UC)
- Passport cookies present but **expired** (`OauthExpires` 2026-08-06) — `hasAuth=false`
- `GOOGLE_PASSWORD` set; Google SSO helper ran (cookie banner dismissed; Continue with Google clicked)
- Google FedCM password page: fill reported ok but session never reached Indeed account settings (`sso_unconfirmed`)
- No `ASK_OWNER_GOOGLE_2FA` challenge (stayed on `/signin/challenge/pwd` or bounced to Indeed `/auth`)
- Artifacts: `/opt/cursor/artifacts/indeed-google-sso-unconfirmed.png`, `indeed-daily-run.json`, `indeed-preflight.json`

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** |
| Skipped | 0 |
| Seen | 0 (stopped at login) |
| Blocked | 1 (`indeed_login_required` / `sso_unconfirmed`) |

Round 2 (false signed-in) briefly scanned 5 company-site jobs as anonymous `did_not_leave_indeed` — **not counted as applies**. That run was stopped.

## Code fix (this run, not yet on main — PR create gated)
- `tools/indeed/google_sso.py`: dismiss OneTrust; JS-click Google CTA; strict signed-in (no auth-form `email address`); native+keystroke password; second Google click on bounced `/auth`
- Tests: `tools/indeed/test_filters.py`
- Issues: `automation-prompts/issues/indeed.md`

## Owner action (required before applies)
1. Desktop Chrome Default: sign in to **https://in.indeed.com** (Google SSO / 2FA on your phone).
2. `bash scripts/sync-chrome-sessions.sh` then **Save Snapshot** so cloud Passport is live.
3. Optional: home Wi‑Fi `scripts/indeed-home-daily.sh` or residential `INDEED_HTTP_PROXY`.
4. Merge branch `cursor/indeed-daily-post-fix-re-run-2026-09-02-8146` when the PR approval prompt is accepted.

Resume used: `/workspace/resumes/Rafi_Resume.docx`.
