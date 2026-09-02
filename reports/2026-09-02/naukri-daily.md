# Naukri daily — 2026-09-02 (post-fix re-run)

Same-day re-run on merged `main` (`ddec99e`, PR #309). `POST_FIX_RERUN=1`.
Agent: https://cursor.com/agents/bc-f2e2e66c-a004-421d-a7f8-e15de1d8923c

## Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied (runner): **4**
- honest new .NET-fit applies: **1** (Highradius) — 3 runner applies were non-.NET false Quick Applies (fixed this run)
- externalCompleted: **0**
- blocked: **1**
- skipped: 3200 (dup-heavy) · seen: 215 · tailoredApplies: 4
- already_applied_detail: Clean Harbors `.Net TEchnical Architect`; Sidgs Digisol `Apigee Architect`

## Profile resume refresh (STEP 0)
- ok: true · matchedToken: Uploaded today · resume: `Rafi_Resume.docx`
- path: toptier-filechooser `#attachCV` / Update
- profile restored to canonical `Rafi_Resume.docx` at end of run

## Applied (runner-confirmed Naukri CTA)

| Company | Role | Path | Resume | Note |
| --- | --- | --- | --- | --- |
| Redbox HR Consulting | Azure Architect | Naukri Quick Apply (`chatbot:responses_thanks`) | tailored `Rafi_Resume.docx` | **False apply** — Databricks / Fabric / GenAI / Python JD, no .NET |
| TechBlocks | Architect - Cloud Platform Engineering | Naukri (`view_applied_jobs`) | tailored `Rafi_Resume.docx` | **False apply** — Terraform / OPA / Python Cloud Platform Engineer |
| Aveva | R&D Senior Member of Technical Staff, Cloud DevOps | Naukri (`view_applied_jobs`) | tailored `Rafi_Resume.docx` | **False apply** — Java/Python Cloud Operations / DevOps |
| Highradius | Principal Product Solution Architect | Naukri (`view_applied_jobs`) | tailored `Rafi_Resume.docx` | Homepage inventory; JD is product SA (Java/Golang/Salesforce listed; no .NET). Counted because uncertain → apply |

- Redbox: https://www.naukri.com/job-listings-azure-architect-redbox-hr-consulting-hyderabad-chennai-bengaluru-11-to-17-years-290826014645?src=directSearch
- TechBlocks: https://www.naukri.com/job-listings-architect-cloud-platform-engineering-techblocks-consulting-pvt-ltd-hyderabad-12-to-17-years-240826920301?src=directSearch
- Aveva: https://www.naukri.com/job-listings-r-d-senior-member-of-technical-staff-cloud-devops-aveva-solutions-india-llp-hyderabad-bengaluru-10-to-15-years-050826934480?src=directSearch
- Highradius: https://www.naukri.com/job-listings-principal-product-solution-architect-highradius-hyderabad-13-to-17-years-010926036390?src=drecomm_dashboard_aurus

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Blackbaud | Software Engineer, Principal - .NET DevOps | `ats_login_wall` (Workday Sign In visible; owner tenant login) | company_ATS Workday |

- https://blackbaud.wd1.myworkdayjobs.com/en-US/ExternalCareers/job/Hyderabad---India-(Skyview)/Software-Engineer--Principal---NET-DevOps_R0014448/apply/autofillWithResume

## Notable skips
- Age-1 inventory thin / already applied this morning → early expand 3+7, then 15/30/60 + extra queries
- Title skips: Data Architect, DevOps Engineer, GenAI/AI Architect, SAP/Salesforce/ServiceNow, etc.
- Incedo `.Net Lead` — `skip_ctc_max_30`
- Hirist walls: none hard-blocked this run
- Thin true .NET title inventory (Clean Harbors already applied; Blackbaud is the main .NET ATS)

## Code fix this run
- `resume_and_filters.js`: JD skip adds `generative ai` + Databricks/Fabric/Synapse/PySpark/ADF hits; title-skip `cloud devops` and `cloud platform engineering`
- `daily_apply.js`: pass 4000-char detail blob into JD skip (1200-char slice missed Redbox GenAI/Databricks)
- Tests in `test_filters.js`
