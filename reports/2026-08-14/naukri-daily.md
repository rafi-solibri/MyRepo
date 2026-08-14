# Naukri daily — 2026-08-14 (post-fix re-run)

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` | Expected 65 LPA / Current 52 LPA | Hyd + Remote

This run used **merged `main`** at `8e4652a` (includes `fix(naukri): skip attack-surface / cybersecurity primary titles` #149). Earlier 2026-08-14 ensure-missing run applied 2 jobs (including Attack Surface Reduction) **without** that filter.

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441

## STEP 0 — Profile resume refresh
- **profileUpdated:** `true` (both passes)
- **verify:** Resume / Update / Rafi_Resume.docx / Uploaded today (`matchedToken: today`, `todayHit: true`)
- **upload:** `input[id*='resume' i][type='file']` → Update
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts
### Pass 1 (merged #149 cyber skip, 08:56–09:45 UTC)
- applied: **12** · externalCompleted: **0** · blocked: **34** · skipped: **2680** (seen 276)
- earlyExpandedAges: `[3, 7]` · expandedAges: `[15, 30, 60]`

### Pass 2 (new title skips in this branch, 09:53–10:09 UTC)
- applied: **2** · externalCompleted: **0** · blocked: **2** · skipped: **471** (seen 69)

**Session total applied: 14** (Naukri Quick Apply / chatbot thanks — not invented)

## Applied (path: Naukri, resume: `Rafi_Resume.docx`)
| Pass | Company | Role | Location | Notes |
| --- | --- | --- | --- | --- |
| 1 | Movate Technologies | Data Solution Architect | Hybrid Hyd/Chennai/Bengaluru | false-apply → filter |
| 1 | PwC | Azure/AWS Architect-Manager with Snowflake and Banking domain | Hybrid Hyd/Kolkata/Bengaluru | cloud architect |
| 1 | Tata Consultancy Services | Azure AI ML Architect | Hyd/Chennai/Bengaluru | false-apply → filter |
| 1 | Clean Harbors | Architect - Mobile Applications | Hyderabad | architect |
| 1 | Luxury Screens | Marketing Director - Head of Marketing | Remote | false-apply → filter |
| 1 | Tredence | Dot Net Architect | Hybrid Hyd/Pune/Bengaluru | on-stack |
| 1 | Hexaware Technologies | Data Platform Solution Architect | Hybrid Hyd/Chennai/Bengaluru | false-apply → filter |
| 1 | MANEVA CONSULTING PRIVATE LIMITED | Oracle C2M Solution Architect | Hyd/Pune/Bengaluru | false-apply → filter |
| 1 | SHI | Senior Solution Architect Network & Security | Hyderabad | false-apply → filter |
| 1 | other | JIRA Atlassian Architect | Hybrid Hyd/Chennai/Bengaluru | false-apply → filter |
| 1 | Leading Consumer Products GCC | Endpoint Architect | Hybrid Hyd (HITEC City) | false-apply → filter |
| 1 | Trackmind Solutions | Pricing Architect | Hyd/Mumbai/Pune | false-apply → filter |
| 2 | Naukri Assist | Azure Cloud Solution Architect | Hyderabad, Delhi / NCR | cloud SA |
| 2 | Tata Consultancy Services | TOSCA Automation Architect | Hyd/Noida/Mumbai | false-apply → TOSCA skip |

Already-applied skipped (not re-applied): i2e Consulting Solution Architect; Clean Harbors .Net Fullstack Tech Lead. Attack Surface Reduction from the earlier run was not re-applied.

## Blocked
Pass 1: 7× `apply_unconfirmed`, 24× `external_incomplete_or_timeout`, 3× Medtronic `ats_login_wall`. On-stack unconfirmed: NTT DATA Lead .NET Full Stack Developer; Experian Lead Software Engineer(.Net + AWS).
Pass 2: Synechron Artificial Intelligence Architect (`apply_unconfirmed`); staffing AI Architect (`quick_apply_not_found`).

## Skip reasons (pass 1)
duplicate_in_run 2450 · skip_title_keyword 131 · skip_seniority 47 · skip_no_dotnet 39 · skip_ctc_max_30 8 · already_applied_detail 2

## Code fix (new blockers from this re-run)
`tools/naukri/resume_and_filters.js` + `test_filters.js`:
- SKIP: marketing, pricing architect, process engineer, Atlassian/Jira, endpoint architect, network & security, cyber architecture, TOSCA
- PURE_AI_DATA: AI ML architect, artificial intelligence, data architect / data solution / data platform SA
- NON_DOTNET_PRIMARY: `\boracle\b` (Oracle C2M)

PR create via `gh` failed (`Resource not accessible by integration`). Branch pushed: `cursor/naukri-daily-post-fix-re-run-2026-08-14-67c0`.

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply-postfix-1.json` (pass 1)
- `/opt/cursor/artifacts/naukri-daily-apply.json` (pass 2)

## Earlier same-day run (ensure-missing, pre-#149)
- Applied: Nopal Support Services — Senior Manager - Attack Surface Reduction; Big 4 Accounting Firms — Dotnet Full stack with AI Manager
