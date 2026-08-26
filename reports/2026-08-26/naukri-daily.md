# Naukri daily — 2026-08-26 (post-fix re-run)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
This run: https://cursor.com/agents/bc-dd828e3d-6e7e-4b4f-b5bc-b101cd94c62f
Merged fix applied: https://github.com/rafi-solibri/MyRepo/pull/269 (`1348367` on `main`)
Earlier morning run (applied **before** the fix): https://cursor.com/agents/bc-bc60054e-b58c-4331-9b67-fae3aa726d56

`POST_FIX_RERUN=1`. Date=2026-08-26 IST. No new post-fix re-run launched (no new code-fixable blocker; re-run cap not consumed further).

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

Skip reasons: `duplicate_in_run` 2708 · `skip_title_keyword` 148 · `skip_seniority` 30 · `skip_no_dotnet` 25 · `skip_jd_non_dotnet_detail` 6 · `skip_company` 5 · `skip_location` 5 · `skip_ctc_max_30` 4 · `already_applied_detail` 1 · `hirist_login_required_skip` 1 · `skip_ctc_max_32.5` 1

No applies were invented. Jobs already submitted today were not re-submitted.

## Already applied earlier today (morning run, do not re-count)
All Naukri Quick Apply, tailored `Rafi_Resume.docx`:

1. Techno Comp TCI — Dot Net Technical Architect — [250826020570](https://www.naukri.com/job-listings-dot-net-technical-architect-techno-comp-tci-hyderabad-10-to-20-years-250826020570)
2. Anlage Infotech / Big 4 — AWS Dot Net Architect — [250826029932](https://www.naukri.com/job-listings-aws-dot-net-architect-anlage-infotech-hyderabad-10-to-16-years-250826029932)
3. Anlage Infotech / BIG4 — AWS Architect - Manager — [260826000063](https://www.naukri.com/job-listings-aws-architect-manager-anlage-infotech-hyderabad-10-to-13-years-260826000063)
4. PepsiCo — Architect - Enterprise Solutions Sr. Analyst — [310726916007](https://www.naukri.com/job-listings-architect-enterprise-solutions-sr-analyst-pepsico-global-business-services-india-llp-hyderabad-11-to-12-years-310726916007)
5. Xtrm India — Software Application Architect — [170226022233](https://www.naukri.com/job-listings-software-application-architect-xtrm-india-chennai-10-to-15-years-170226022233)

Also skipped this session as already applied: **Clean Harbors — .Net Fullstack Tech Lead** (`already_applied_detail`).

Morning blocked (not re-attempted as new applies): Tech Mahindra Netcool Architect (`apply_unconfirmed`); Thermo Fisher Staff Engineer Workday login wall; Cadence Principal Design Engineer Workday timeout.

## PR #269 verification on this run
- **Cadence / Principal Design Engineer** → `skip_company` (no ATS burn)
- **Netcool Architect** not in this re-run’s inventory (already attempted this morning)
- No false applies, no blocked attempts

## Why 0 new applies
After the morning 5 Quick Applies, remaining Hyd/remote cards were title/company/JD skips (Java/Python/AI/Salesforce/SAP/ServiceNow/QA/cyber), seniority IC roles, CTC max &lt; 35 LPA (e.g. Incedo .Net Lead `skip_ctc_max_30`), one Hirist login wall (skipped, not hard-blocked), or already applied. Thin eligible .NET Architect/Lead inventory; expanded ages 15/30/60 + extra queries + recommended/homepage.

## Combined 2026-08-26 Naukri totals (morning + this re-run)
- Profile resume: updated today (`Rafi_Resume.docx`)
- **Applied: 5** (all morning; 0 additional here)
- External completed: 0
- Blocked (morning only): 3
- This re-run blocked: 0

Artifact: `/opt/cursor/artifacts/naukri-daily-apply.json`  
Summary copy: `reports/2026-08-26/naukri-daily-apply-summary.json`
