# Hitech City / Knowledge City daily — 2026-08-24 (post-fix re-run after #245)

## Totals
- **Submitted: 0** (confirmation text only — none invented)
- Referrals: 0 | Blocked: 13 | Skipped: 13 | Scanned: 98
- Report: `/opt/cursor/artifacts/[REDACTED]-daily.json`
- Mode: `POST_FIX_RERUN=1` + careers-only on merged `main` `8b29a84` (#245 resume refresh)
- Parallel careers: 10 tabs (`CAREERS PARALLEL start tabs=10`)
- Resume: JD-tailored `Rafi_Resume.docx` from refreshed `Mohammed_Abdul_Rafi_Ahmed_Resume` master

## Phases
| Phase | Result |
| --- | --- |
| Discovery | 92 companies (0 added, 92 updated) |
| Careers parallel (10 tabs) | 0 applied / 13 blocked / 13 skipped / 98 scanned |
| LinkedIn + referrals | skipped (careers-only; live LinkedIn CDP still `linkedin_login_required`) |
| Boards | skipped (careers-only) |

## Careers blocked (all NOT_SUBMITTED)
- JPMorgan Chase ×3 — CAPTCHA/bot wall (Lead Software Engineer Hyderabad)
- Experian ×3 — CAPTCHA/bot wall (Solutions Architect / Director of Engineering Hyd)
- ModMed ×3 — ats_login_wall (Principal Cloud Engineer / Senior Software Architect Hyd)
- Oracle ×3 — ats_otp_wall + external_incomplete_or_timeout (Senior Principal FDE / Principal Core Infra Hyd)
- Gartner ×1 — ats_login_wall on **wrong-region** "Sr Director Analyst … AI Strategy … (Remote - N.A.)" (Workday `Remote---United-States`)

## Careers skipped
- Solera — Workday no Hyderabad facet
- Apple / Goldman Sachs / Meta — hang_scan_host
- Optum / UHG — skip_uhg

## Owner actions needed
1. LinkedIn headed login / CAPTCHA: `bash scripts/home-headed-login.sh linkedin`
2. Solve career-portal CAPTCHAs when awake (JPMC Oracle Cloud, Experian SmartRecruiters)
3. ModMed Workday Sign In + Oracle email OTP (guest apply)

## Code fix from this re-run
- Gartner `(Remote - N.A.)` / Workday `Remote---United-States` + `AI Strategy` title false-passed as India-remote / campus-eligible
- `BAD_LOC_HINT` now matches Remote-N.A. / North America; AIML + careers + LinkedIn title skips add `AI Strategy`
