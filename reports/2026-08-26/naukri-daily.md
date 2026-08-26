# Naukri daily — 2026-08-26 (second post-fix re-run)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
This run: https://cursor.com/agents/bc-117fae61-092f-4195-a569-ddff4847860e
`POST_FIX_RERUN=1`. Date=2026-08-26 IST. Head: `4fd61ce` on `main`.

Triggered because merged https://github.com/rafi-solibri/MyRepo/pull/270 (`tools/ats/email_otp.py` is shared apply infra). Naukri filter fix https://github.com/rafi-solibri/MyRepo/pull/269 was already applied by the first post-fix re-run.

Prior runs today:
- Morning (applied **before** #269): https://cursor.com/agents/bc-bc60054e-b58c-4331-9b67-fae3aa726d56
- First post-fix re-run (on #269, 0 new applies): https://cursor.com/agents/bc-dd828e3d-6e7e-4b4f-b5bc-b101cd94c62f

No new code-fixable Naukri blocker. No further post-fix re-run launched (2 of 5 same-day cap used).

## STEP 0 — profile resume refresh
- **ok** — `profileUpdated: true`
- Token: **Uploaded today**
- Resume filename shown: **Rafi_Resume.docx** (rebuilt from `resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx`; upload 20945B)
- Profile restored to canonical CV at end of run: **ok**

## This re-run counts
| metric | count |
| --- | --- |
| profileUpdated | true |
| applied (new, this session) | **0** |
| external completed | 0 |
| blocked | 0 |
| skipped | 2934 |
| seen | 204 |
| tailoredApplies | 0 |
| queriesRun | 288 |

Skip reasons: `duplicate_in_run` 2708 · `skip_title_keyword` 148 · `skip_seniority` 30 · `skip_no_dotnet` 25 · `skip_jd_non_dotnet_detail` 6 · `skip_company` 5 · `skip_location` 5 · `skip_ctc_max_30` 4 · `already_applied_detail` 1 · `hirist_login_required_skip` 1 · `skip_ctc_max_32.5` 1

Ages: primary 1/3/7, early-expand 3/7, expand 15/30/60, plus extra .NET/Azure queries + recommended/homepage. No applies were invented. Jobs already submitted today were not re-submitted.

## Already applied earlier today (do not re-count)
All Naukri Quick Apply, tailored `Rafi_Resume.docx` (morning run):

1. Techno Comp TCI — Dot Net Technical Architect — [250826020570](https://www.naukri.com/job-listings-dot-net-technical-architect-techno-comp-tci-hyderabad-10-to-20-years-250826020570)
2. Anlage Infotech / Big 4 — AWS Dot Net Architect — [250826029932](https://www.naukri.com/job-listings-aws-dot-net-architect-anlage-infotech-hyderabad-10-to-16-years-250826029932)
3. Anlage Infotech / BIG4 — AWS Architect - Manager — [260826000063](https://www.naukri.com/job-listings-aws-architect-manager-anlage-infotech-hyderabad-10-to-13-years-260826000063)
4. PepsiCo — Architect - Enterprise Solutions Sr. Analyst — [310726916007](https://www.naukri.com/job-listings-architect-enterprise-solutions-sr-analyst-pepsico-global-business-services-india-llp-hyderabad-11-to-12-years-310726916007)
5. Xtrm India — Software Application Architect — [170226022233](https://www.naukri.com/job-listings-software-application-architect-xtrm-india-chennai-10-to-15-years-170226022233)

Also skipped this session as already applied: **Clean Harbors — .Net Fullstack Tech Lead** (`already_applied_detail`).

Hirist login wall (Rapidue Solution Architect) skipped, not hard-blocked.

## Shared #270 ATS OTP fix
No company-site / Workday OTP wait ran this session (0 external). The Gmail Sign-in abort in `tools/ats/email_otp.py` was present on `main` and unused because remaining inventory was already-applied or filter-skipped.

## PR #269 verification (still holds)
- **Cadence / Principal Design Engineer** → `skip_company` (no ATS burn)
- Salesforce TA / DevOps TA / Manager titles → `skip_company`
- Incedo `.Net Lead` still `skip_ctc_max_30` (band &lt; 35 LPA)

## Combined 2026-08-26 Naukri totals
- Profile resume: updated today (`Rafi_Resume.docx`)
- **Applied: 5** (all morning; 0 additional on either post-fix re-run)
- External completed: 0
- Blocked: 3 (morning only: Tech Mahindra Netcool `apply_unconfirmed`; Thermo Fisher Workday login wall; Cadence Workday timeout — Cadence now skip_company)
- This re-run blocked: 0

Naukri daily does not send the status email; Notification Job 11 AM compiles portal results.

Artifact: `/opt/cursor/artifacts/naukri-daily-apply.json`  
Summary copy: `reports/2026-08-26/naukri-daily-apply-summary.json`
