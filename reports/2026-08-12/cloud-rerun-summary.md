# Cloud job automation rerun - 2026-08-12

## Why the scheduled runs failed

The 9 AM cloud automations did run, but several portal agents hit a shared
preflight regression before applying:

- `tools/chrome_session.js` contained a Python-style `def checkPortal`, which
  made Node fail with a syntax error during `preflight-portal-run.sh`.
- `scripts/resolve-python.sh` expanded `$LOCALAPPDATA` under `set -u` on Linux,
  aborting some preflights after session sync.

Those helper fixes were already merged to `main` before this rerun:

- `function checkPortal(portal)` is restored in `tools/chrome_session.js`.
- `resolve-python.sh` now guards `${LOCALAPPDATA:-}`.
- Hitech City / Naukri / Instahyre / Foundit follow-up fixes through PR #92 are
  also present on `main`.

## Rerun command path

Fetched latest `main`, verified all seven portal preflights, then reran the
portal apply commands sequentially in cloud:

1. LinkedIn
2. Foundit
3. Cutshort
4. Naukri
5. Instahyre
6. Indeed
7. Hitech City / Knowledge City

All preflights passed after the merged fixes. Indeed's WARP + SeleniumBase UC
Cloudflare preflight also cleared successfully.

## Rerun results

| Portal | Applied | External | Blocked / rejected | Skipped | Seen | Notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| LinkedIn | 0 | 0 | 22 blocked | 4 | - | Easy Apply blocked by live LinkedIn login (`linkedin_login_required`); external ATS fallback had 21 time-cap/account-wall blocks. |
| Foundit | 0 | 0 | 0 | 509 | - | Logged in. No new qualifying submissions because today's qualifying Foundit jobs were already applied in the earlier fixed run. |
| Cutshort | 0 | 0 | 323 locked-empty questionnaire states | 0 | 1968 | No qualifying jobs found; report written to `reports/2026-08-12/cutshort-daily.md`. |
| Naukri | 0 | 0 | 7 | 2466 | 350 | Profile resume refresh succeeded and verified as uploaded today. Remaining blocks are ATS/account/password-policy style blockers. |
| Instahyre | 2 | 0 | 0 | 669 | 671 | Submitted through Instahyre in-app API. |
| Indeed | 3 | 0 | 1 blocked, 6 rejected/incomplete | 14 | 25 | WARP+UC cleared Cloudflare; three Easy Apply submissions completed, one reCAPTCHA block remained. |
| Hitech City / Knowledge City | 0 | 0 | 7 | 8 | 18 careers scanned | LinkedIn phase blocked by live LinkedIn login; career portals hit Amazon account walls and Qualcomm ATS incomplete/stuck states. |

Total new submissions in this rerun: **5**.

## Remaining actions

- Refresh LinkedIn login in the saved cloud session/snapshot. Both LinkedIn and
  the LinkedIn-backed Hitech City phase are blocked by a stale live session even
  when cookie names are present.
- For Naukri Workday-style ATS flows, keep `NAUKRI_WORKDAY_PASSWORD` at 12+
  characters with upper/lower/number/special; short secrets trigger password
  policy blocks.
- Indeed is operational in cloud with WARP+UC, but still has residual
  SmartApply reCAPTCHA/incomplete-form blockers on some jobs.
