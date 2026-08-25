# Hitech City / Knowledge City daily — 2026-08-25 (post-fix re-run)

SAME-DAY POST-FIX RE-RUN (`POST_FIX_RERUN=1`) on merged `main` after [#257](https://github.com/rafi-solibri/MyRepo/pull/257). Earlier morning run hit the preflight `sync-chrome-sessions.sh` hirist DEST/cookie array blocker and did **not** apply with the fix. This job pulled `main` @ `c507fd2` and executed career-portal applies.

## Status
**Careers-only run completed.** Confirmation applies only (no invented counts).

- **Submitted: 0** | Referrals: 0 | Blocked: 9 | Skipped: 14 | Scanned: 90
- Mode: careers-only, 10 parallel Chrome tabs
- Resume: `resumes/Rafi_Resume.docx` (label **Rafi_Resume**, 3,957,700 bytes)
- LinkedIn + boards skipped this re-run (do not wait on LinkedIn CAPTCHA)
- Artifact: `/opt/cursor/artifacts/` daily + careers JSON from this run

## Phases
| Phase | Result |
| --- | --- |
| Preflight | **OK** after #257 — LinkedIn `li_at` present; resume ready; hirist seed still missing (unused here) |
| Chrome CDP | Careers-only: skipped WARP + LinkedIn auto-login; CDP ready on `:9222` |
| Discovery | 92 companies (0 added, 92 updated); LinkedIn discovery off |
| Careers parallel (10 tabs) | 0 applied / 9 blocked / 14 skipped / 90 scanned |
| LinkedIn + referrals | skipped (careers-only) |
| Boards | skipped (careers-only) |

## Applied (confirmation text)
None. No ATS / career-portal confirmation banner this run.

## Careers blocked (not submitted)
- **JPMorgan Chase** ×3 — Lead Software Engineer Hyderabad — `CAPTCHA/bot wall` (Oracle Cloud apply/email)
- **Experian** ×3 — Lead Software Engineer Mainframe / Director of Engineering / Senior Staff Software Engineer (Hyd) — `CAPTCHA/bot wall` (SmartRecruiters OneClick)
- **ModMed** ×3 — Principal Cloud Engineer / Senior Software Architect (Hyd) — `ats_login_wall` (Workday `/login`)

## Careers skipped
- Intel, Solera — `workday_no_hyderabad_facet`
- Apple, Goldman Sachs, Meta — `hang_scan_host` (known starve-avoidance)
- Optum / UHG — campus UHG skip

## Owner actions (not code-fixable)
1. Solve JPMC Oracle Cloud + Experian SmartRecruiters CAPTCHAs headed (`scripts/home-headed-careers-apply.sh`)
2. ModMed Workday login (or guest apply) for Hyd Principal Cloud / Senior Architect
3. LinkedIn headed login still needed before a non-careers-only pass (`scripts/home-headed-login.sh linkedin`)

## Auto-fix
No **new** code-fixable blocker this re-run. Preflight/CDP/discovery/parallel careers all executed on merged main. Empty job counts on Oracle/Hyland/Gartner/Accenture after location pin match the 2026-08-21 cloud/headless inventory pattern (no crash / no helper regression). Post-fix re-run count for this portal today: **1 / 5**.
