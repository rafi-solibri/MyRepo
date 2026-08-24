# Hitech City / Knowledge City daily — 2026-08-24 (post-fix re-run after #252)

## Totals
- **SUBMITTED: 0** (confirmation text only — none invented) | Referrals: 0 | Blocked: 12 | Skipped: 14
- Discovery: 92 companies (0 added)
- Mode: `POST_FIX_RERUN=1` + `HITECHCITY_CAREERS_ONLY=1` + `HITECHCITY_PARALLEL_TABS=10`
- Code: `main` @ `5fb6c1b` — `fix(hitechcity): skip Remote N.A. roles and pin Salesforce location select (#252)`
- Resume: `resumes/Rafi_Resume.docx` (JD-tailored per ATS attempt)
- Report: `/opt/cursor/artifacts/hitechcity-daily.json`
- Log: `/opt/cursor/artifacts/hitechcity-daily-apply.log`
- Chat log: `/opt/cursor/artifacts/hitechcity-apply-chat.jsonl`

## Phases
| Phase | Result |
| --- | --- |
| Discovery | 92 companies (0 added, 92 updated) |
| Careers parallel (10 tabs) | 0 applied / 12 blocked / 14 skipped / 90 scanned |
| LinkedIn + referrals | skipped (`HITECHCITY_CAREERS_ONLY=1` — do not wait on LinkedIn CAPTCHA) |
| Boards | skipped (careers-only) |

## #252 fix evidence (this re-run used merged code)
- Gartner `Remote - N.A.` titles were **not** opened (filter now treats N.A./North America as foreign).
- DXC location UI pinned via `native_select:Hyderabad`.
- Salesforce scanned with `city=Hyderabad` in URL; on-page pin was `button_menu_no_hyd`; extracted **0** matching Hyd EM/TL/Staff/Principal roles (not invented).

## Careers blocked (owner-only — not code-fixable)
- JPMorgan Chase ×3 — CAPTCHA/bot wall (Lead Software Engineer Hyderabad)
- Experian ×3 — CAPTCHA/bot wall (Solutions Architect / Director of Engineering · Hyderabad)
- ModMed ×3 — `ats_login_wall` (Principal Cloud Engineer / Senior Software Architect · Hyderabad)
- Oracle ×1 — `ats_otp_wall` (Senior Principal FDE HYDERABAD)
- Oracle ×2 — `external_incomplete_or_timeout` (Principal Core Infrastructure Engineer HYDERABAD)

## Skipped
- Intel / Solera — `workday_no_hyderabad_facet`
- Apple / Goldman Sachs / Meta — `hang_scan_host`
- Remaining scanned tenants: 0 matching Hyd cards after location pin

## Owner actions needed
1. Solve career-portal CAPTCHAs (JPMC Oracle Cloud, Experian SmartRecruiters) on a headed session
2. ModMed Workday login: `bash scripts/home-headed-login.sh` / Workday credentials
3. Oracle email OTP on `careers.oracle.com` apply/email

## Same-day re-run cap
This is post-fix re-run **4 of 5** for hitechcity on 2026-08-24 IST. Remaining blockers are CAPTCHA / login / OTP (owner-only). No new code-fixable blocker launched another re-run.
