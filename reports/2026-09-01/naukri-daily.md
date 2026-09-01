# Naukri daily — 2026-09-01 (post-fix re-run)

Same-day re-run on merged `main` after [PR #304](https://github.com/rafi-solibri/MyRepo/pull/304) (`cebaf8a` title-skip Oracle PaaS/HCM/ERP, Fusion HCM, IMDS, DFT). Morning cron applied **before** that fix; this job executed `node tools/naukri/daily_apply.js` with the merged filters. `POST_FIX_RERUN=1`. Re-run count for naukri today: **1 / 5**.

## Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied: **2**
- externalCompleted: **0**
- blocked: **4**
- skipped: 3178 (dup-heavy) · seen: 202 · tailoredApplies: 2

## Profile resume refresh
- ok: true · matchedToken: Uploaded today · resume: Rafi_Resume.docx
- path: toptier-filechooser `#attachCV` / Update
- profile restored to canonical `Rafi_Resume.docx` at end of run

## Applied
| Company | Role | Path | Resume |
| --- | --- | --- | --- |
| enGen Global (Thryve Digital Health LLP) | Advisor - Senior Solution Architect | Naukri Quick Apply (`view_applied_jobs`) | tailored `/tmp/naukri-tailored/23cb31941305/Rafi_Resume.docx` |
| D E Shaw | Principal Architect (Management Company Tech) | Naukri Quick Apply (`view_applied_jobs`) | tailored `/tmp/naukri-tailored/047c2609e6e2/Rafi_Resume.docx` |

- enGen: https://www.naukri.com/job-listings-advisor-senior-solution-architect-thryve-digital-health-llp-hyderabad-chennai-9-to-12-years-180826942609?src=directSearch · Hyd/Chennai · query `solution architect` · age 15d
- D E Shaw: https://www.naukri.com/job-listings-principal-architect-management-company-tech-d-e-shaw-india-private-limited-hyderabad-gurugram-bengaluru-8-to-13-years-100826921356?src=directSearch · Hyd/Gurugram/Bengaluru · query `principal engineer` · age 30d

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Bharathire.com | Technical Architect | apply_unconfirmed | Naukri |
| Optum / UnitedHealth | Manager Software Engineering - Dot Net FSD+ Angular Must | external_incomplete_or_timeout | company_ATS UHG careers |
| Blackbaud | Software Engineer, Principal - .NET DevOps | ats_login_wall | company_ATS Workday |
| Capgemini | Enterprise Architect | apply_unconfirmed | Naukri |

- Bharathire: https://www.naukri.com/job-listings-technical-architect-bharathire-com-private-limited-hyderabad-bengaluru-9-to-14-years-310826913236?src=directSearch
- Optum: https://careers.unitedhealthgroup.com/job/hyderabad/manager-software-engineering-dot-net-fsd-angular-must/34088/99188968688
- Blackbaud: https://blackbaud.wd1.myworkdayjobs.com/en-US/ExternalCareers/job/Hyderabad---India-(Skyview)/Software-Engineer--Principal---NET-DevOps_R0014448/apply/autofillWithResume
- Capgemini: https://www.naukri.com/job-listings-enterprise-architect-capgemini-technology-services-india-limited-hyderabad-15-to-20-years-310826918569?src=drecomm_dashboard_aurus

Blackbaud Workday is the same listing blocked 2026-08-31 (`ats_password_policy`); today's Sign In fallback reached `ats_login_wall` (owner tenant login / 2FA — not a new code-fixable). Optum UHG timed out. Two Naukri CTAs never flipped to Applied.

## Notable skips
- Clean Harbors — .Net TEchnical Architect — already_applied_detail (skipped; already submitted)
- Sidgs Digisol — Apigee Architect — already_applied_detail
- Incedo — .Net Lead — skip_ctc_max_30 (<35 LPA floor)
- Leading Client — .NET Full Stack Developer — skip_seniority
- Cisco — ASIC DFT Engineering Technical Leader — skip_title_keyword (**#304 fix held**)
- Naukri Assist — Lead Cloud Infrastructure — skip_title_keyword (**#304 Cloud Infra skip held**)
- MANEVA — Oracle Fusion Technical - Reporting Lead — skip_title_keyword
- Thin .NET title inventory (Incedo .Net Lead / Clean Harbors / Blackbaud / Leading Client .NET FSD); early+age 15/30/60 + extra query expand ran

## Code fix this run
None. Ran with already-merged #304. No new code-fixable blocker; did not launch another post-fix re-run.
