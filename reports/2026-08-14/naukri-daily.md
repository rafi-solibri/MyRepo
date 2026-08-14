# Naukri daily — 2026-08-14 (post-fix re-run)

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` | Expected 65 LPA / Current 52 LPA | Hyd + Remote

This run used **merged `main`** at `8e4652a` (includes `fix(naukri): skip attack-surface / cybersecurity primary titles` #149). Earlier 2026-08-14 ensure-missing run applied 2 jobs (including Attack Surface Reduction) **without** that filter.

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441

## STEP 0 — Profile resume refresh
- **profileUpdated:** `true`
- **verify:** Resume / Update / Rafi_Resume.docx / Uploaded today (`matchedToken: today`, `todayHit: true`)
- **upload:** `input[id*='resume' i][type='file']` → Update
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts (this post-fix re-run)
- profileUpdated: **true**
- applied: **12** (Naukri Quick Apply / chatbot thanks — not invented)
- externalCompleted: **0**
- blocked: **34**
- skipped: **2680** (seen 276)
- earlyExpandedAges: `[3, 7]`
- expandedAges: `[15, 30, 60]`

## Applied this re-run (path: Naukri, resume: `Rafi_Resume.docx`)
| Company | Role | Location | Notes |
| --- | --- | --- | --- |
| Movate Technologies | Data Solution Architect | Hybrid Hyd/Chennai/Bengaluru | false-apply → new filter |
| PwC | Azure/AWS Architect-Manager with Snowflake and Banking domain | Hybrid Hyd/Kolkata/Bengaluru | cloud architect |
| Tata Consultancy Services | Azure AI ML Architect | Hyd/Chennai/Bengaluru | false-apply → new filter |
| Clean Harbors | Architect - Mobile Applications | Hyderabad | architect |
| Luxury Screens | Marketing Director - Head of Marketing | Remote | false-apply → new filter |
| Tredence | Dot Net Architect | Hybrid Hyd/Pune/Bengaluru | on-stack |
| Hexaware Technologies | Data Platform Solution Architect | Hybrid Hyd/Chennai/Bengaluru | false-apply → new filter |
| MANEVA CONSULTING PRIVATE LIMITED | Oracle C2M Solution Architect | Hyd/Pune/Bengaluru | false-apply → new filter |
| SHI | Senior Solution Architect Network & Security | Hyderabad | false-apply → new filter |
| other | JIRA Atlassian Architect | Hybrid Hyd/Chennai/Bengaluru | false-apply → new filter |
| Leading Consumer Products GCC | Endpoint Architect | Hybrid Hyd (HITEC City) | false-apply → new filter |
| Trackmind Solutions | Pricing Architect | Hyd/Mumbai/Pune | false-apply → new filter |

Already-applied skipped (not re-applied): i2e Consulting Solution Architect; Clean Harbors .Net Fullstack Tech Lead. Attack Surface Reduction from the earlier run was not re-applied (already submitted today; cyber title now also skipped).

## Blocked (sample)
- 7× `apply_unconfirmed` (Naukri chat/drawer)
- 24× `external_incomplete_or_timeout` (Workday/Keka/Oracle Cloud/SmartRecruiters/etc.)
- 3× Medtronic `ats_login_wall` (Workday Sign In)
- Notable on-stack unconfirmed: NTT DATA Lead .NET Full Stack Developer; Experian Lead Software Engineer(.Net + AWS)

## Skip reasons (top)
- duplicate_in_run: 2450
- skip_title_keyword: 131 (SAP/Java/Salesforce/QA/SRE/cyber/data-engineer/…)
- skip_seniority: 47
- skip_no_dotnet: 39
- skip_ctc_max_30: 8
- already_applied_detail: 2
- skip_ctc_max_32.5: 2
- skip_ctc_max_31: 1

## Code fix (new blocker from this re-run)
ARCH_LEAD waiver (`director` / `head of` / bare `architect`) plus incomplete AI/data/Oracle/security title skips caused non-.NET applies. Updated `tools/naukri/resume_and_filters.js` + `test_filters.js`:
- SKIP: marketing, pricing architect, process engineer, Atlassian/Jira, endpoint architect, network & security, cyber architecture
- PURE_AI_DATA: AI ML architect, data architect / data solution / data platform SA
- NON_DOTNET_PRIMARY: `\boracle\b` (Oracle C2M)

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`

## Earlier same-day run (ensure-missing, pre-#149)
- Applied: Nopal Support Services — Senior Manager - Attack Surface Reduction; Big 4 Accounting Firms — Dotnet Full stack with AI Manager
