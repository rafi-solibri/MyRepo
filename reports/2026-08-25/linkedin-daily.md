# LinkedIn daily — 2026-08-25

## Status
**STOPPED** — LinkedIn login required after same-day post-fix re-run on merged `main`. **0** confirmed applies (none invented).

## Post-fix re-run (this job)
Executed `POST_FIX_RERUN=1` on 2026-08-25 IST with merged code (`origin/main` including #257 / #258). Goal was to apply with the preflight fix the morning cron never used.

- `git fetch/checkout/pull` main, then `bash scripts/preflight-portal-run.sh linkedin` — **OK**
  - Resume `Rafi_Resume.docx` ready (canonical + `/home/ubuntu/resumes` + Documents aliases)
  - `sourceHasAuth` / `destHasAuth` for LinkedIn `li_at` cookie **names** OK (hirist dest/token mismatch already on main)
- `bash scripts/launch-chrome-cdp.sh linkedin` — WARP SOCKS up; Chrome CDP ready
- Live session: stale `li_at` → `/uas/login` (exit 5). Auto-login:
  1. Google SSO clicked → timed out (GSI fell through to identifier; Google cookie *names* present but session stale)
  2. LinkedIn password candidate 1 of 2 → `/checkpoint/challenge` **Security Verification** reCAPTCHA (exit **6**)
- Recovery (Google SSO only, no further LinkedIn password): identifier form filled; **both** secret candidates rejected by Google (`Wrong password. Try again`)
- `GOOGLE_PASSWORD` unset; `LINKEDIN_PASSWORD` (and `NAUKRI_WORKDAY_PASSWORD` alias) rejected by both LinkedIn and Google
- No CAPSOLVER / 2Captcha keys — cannot clear reCAPTCHA in-cloud
- Easy Apply / external ATS **not started** (login wall). No applies invented.

Artifacts:
- `/opt/cursor/artifacts/linkedin-rerun-page-0.png` — Security Verification / I'm not a robot
- `/opt/cursor/artifacts/linkedin-login-before-gsi.png` — LinkedIn `/login`
- `/opt/cursor/artifacts/linkedin-google-popup.png` — Google identifier (stale GSI)
- `/opt/cursor/artifacts/linkedin-google-after-ident-1.png` — Google **Wrong password**
- `/opt/cursor/artifacts/apply-report.json` — blocked, 0 submitted

Sibling same-day post-fix agent `bc-6f2dea6d-f466-4cb8-8266-d653604dc725` also finished idle (same owner login wall). Re-run count today: **2 / 5**. No further code-fix loop.

## Morning cron (before this re-run)
- Preflight initially failed: `sync-chrome-sessions.sh` unbound `DESTS[$i]` after hirist was added — **already fixed on main via #257**
- Live CDP: stale `li_at` → `/uas/login`; auto-login Google SSO timed out; password → Wrong email or password
- Report merged as **#258** (`docs(linkedin): 2026-08-25 daily report — login blocked`)

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **0** |
| External / ATS completed | **0** (not started — login blocked) |
| Skipped | n/a |
| Blocked | login / wrong password / CAPTCHA |

## Code fix
None this re-run. Preflight array mismatch was already on `main`. Login / wrong password / CAPTCHA are **owner-only** (AUTO_FIX.md). Launching another post-fix agent would burn the same wall.

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** and **`GOOGLE_PASSWORD`** — current values are rejected by LinkedIn **and** Google
2. If Security Verification / CAPTCHA persists after secret refresh: `bash scripts/home-headed-login.sh linkedin` then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LinkedIn Daily after secrets + live session are in the environment (do not rely on another unattended password retry)

## False-skip suspects
None (no search/apply inventory processed).
