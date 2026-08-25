# LinkedIn daily — 2026-08-25

## Status
**STOPPED** — LinkedIn login required after same-day post-fix re-run on merged `main` (`#261`). **0** confirmed applies (none invented).

## Post-fix re-run (this job)
Executed `POST_FIX_RERUN=1` on 2026-08-25 IST with merged code (`5823080` / [PR #261](https://github.com/rafi-solibri/MyRepo/pull/261)). Goal was to apply with the merged helper the earlier runs never used for a live session.

- `git fetch/checkout/pull` main, then `bash scripts/preflight-portal-run.sh linkedin` — **OK**
  - Resume `Rafi_Resume.docx` ready (canonical + `/home/ubuntu/resumes` + Documents aliases; bootstrap compressed upload copy to 20 945 bytes by stripping embedded fonts; owner master `Mohammed_Abdul_Rafi_Ahmed_Resume.docx` left at ~3.9 MB)
  - `sourceHasAuth` / `destHasAuth` for LinkedIn `li_at` cookie **names** OK
- `bash scripts/launch-chrome-cdp.sh linkedin` — WARP SOCKS up; Chrome CDP ready
- Live session: stale `li_at` → `/uas/login` (exit 5). Auto-login:
  1. Google SSO clicked → timed out (`google_session` cookie names present; session stale)
  2. LinkedIn password candidate 1 of 2 → `/checkpoint/challenge` **Security Verification** reCAPTCHA (exit **6**)
- `GOOGLE_PASSWORD` unset as its own secret; `LINKEDIN_PASSWORD` still trips CAPTCHA / is rejected
- No CAPSOLVER / 2Captcha keys — cannot clear reCAPTCHA in-cloud
- Easy Apply / external ATS **not started** (login wall). No applies invented.

Artifacts:
- `/opt/cursor/artifacts/linkedin-rerun3-current.png` — Security Verification / I'm not a robot
- `/opt/cursor/artifacts/linkedin-auto-login-captcha.png` — same checkpoint
- `/opt/cursor/artifacts/linkedin-auto-login-wrong-password.png` — Google identifier **Wrong password**
- `/opt/cursor/artifacts/apply-report.json` — blocked, 0 submitted

Same-day LinkedIn agents that already hit this owner wall:
- Morning cron: https://cursor.com/agents/bc-58fa8bbf-8075-47b3-a40b-a9153783655b
- Re-run 1: https://cursor.com/agents/bc-6f2dea6d-f466-4cb8-8266-d653604dc725
- Re-run 2: https://cursor.com/agents/bc-42219bef-539b-4a71-bc11-6556ed489d9f
- This re-run (3 / 5): https://cursor.com/agents/bc-2ef241f4-3f3d-47f4-a851-1c9842503724

No further code-fix loop. Launching another unattended password retry would only burn the same CAPTCHA.

## Morning cron (before re-runs)
- Preflight initially failed: `sync-chrome-sessions.sh` unbound `DESTS[$i]` after hirist was added — **already on main via #257**
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
None this re-run. Preflight and resume-compress (`#261`) already on `main`. Login / wrong password / CAPTCHA are **owner-only** (`AUTO_FIX.md`).

## Owner action (required before applies)
1. Update Cursor secrets **`LINKEDIN_PASSWORD`** and **`GOOGLE_PASSWORD`** — current LinkedIn password secret is rejected or trips Security Verification
2. Complete headed login after CAPTCHA: `bash scripts/home-headed-login.sh linkedin` then seed refresh / push `.portal-sessions` Cookies (omit Local State)
3. Re-run LinkedIn Daily only after secrets + live session are in the environment (do not rely on another unattended password retry)

## False-skip suspects
None (no search/apply inventory processed).
