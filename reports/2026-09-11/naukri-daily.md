# Naukri daily — 2026-09-11

## Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied: **15** (includes false Quick Applies listed below — title-skips landed same day)
- externalCompleted: **0**
- blocked: **13**
- skipped: 828 (691 duplicate_in_run) · seen: 165 · tailoredApplies: 15

## Profile resume refresh
- ok: true · matchedToken: Uploaded today · resume: Rafi_Resume.docx
- path: toptier-filechooser `#attachCV` / Update
- headline soft-touch: headline_input_missing (upload verify still todayHit)
- profile restored to canonical `Rafi_Resume.docx` at end of run

## Applied
| Company | Role | Path | Resume |
| --- | --- | --- | --- |
| Naukri Assist | Fabric Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored — **false apply** (MS Fabric) |
| Perficient | Technical Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored |
| Sidgs Digisol | Apigee Platform Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored — **false apply** |
| Electrical GCC | Data Solution Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored — **false apply** |
| Newmark Cre Services | Software Engineer Staff | Naukri Quick Apply (chatbot:responses_thanks) | tailored |
| Aspire Systems | Oracle Xstore Solution Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored — **false apply** |
| Naukri Assist | AI Tech Lead | Naukri Quick Apply (chatbot:responses_thanks) | tailored — **false apply** |
| Olam Agri | Engineering Manager | Naukri Quick Apply (chatbot:responses_thanks) | tailored |
| Tata Consultancy Services | AEMaaCS Technical Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored — **false apply** |
| Experis (listed as IT Services & Consulting) | Enterprise Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored |
| Valuelabs | Technical Lead | Naukri Quick Apply (chatbot:responses_thanks) | tailored |
| Simplify Healthcare | Technical Lead | Naukri Quick Apply (chatbot:responses_thanks) | tailored |
| Cognizant | Lead Software Engineer | Naukri Quick Apply (chatbot:responses_thanks) | tailored |
| Nagarro | Principal Engineer (Integration Architect) | Naukri Quick Apply (chatbot:responses_thanks) | tailored |
| Isolved Hcm | Principal Software Engineer, Experience (Vue) | Naukri Quick Apply (chatbot:responses_thanks) | tailored — **false apply** (Vue-primary) |

URLs (Naukri job-listings):
- https://www.naukri.com/job-listings-fabric-architect-naukri-assist-hyderabad-pune-bengaluru-12-to-18-years-100926011682
- https://www.naukri.com/job-listings-technical-architect-perficient-hyderabad-chennai-bengaluru-12-to-16-years-100926035914
- https://www.naukri.com/job-listings-apigee-platform-architect-sidgs-digisol-hyderabad-navi-mumbai-bengaluru
- https://www.naukri.com/job-listings-data-solution-architect-persol-hyderabad-chennai-8-to-
- https://www.naukri.com/job-listings-software-engineer-staff-newmark-cre-services-hyderabad
- https://www.naukri.com/job-listings-oracle-xstore-solution-architect-aspire-systems-hyderabad
- https://www.naukri.com/job-listings-ai-tech-lead-naukri-assist-hyderabad-bengaluru-10-to-2
- https://www.naukri.com/job-listings-engineering-manager-olam-agri-hyderabad-delhi-ncr-beng
- https://www.naukri.com/job-listings-aemaacs-technical-architect-tata-consultancy-services-
- https://www.naukri.com/job-listings-enterprise-architect-experis-hyderabad-chennai-bengalu
- https://www.naukri.com/job-listings-technical-lead-valuelabs-hyderabad-9-to-14-years-09092
- https://www.naukri.com/job-listings-technical-lead-simplify-healthcare-hyderabad-8-to-13-y
- https://www.naukri.com/job-listings-lead-software-engineer-cognizant-hyderabad-12-to-14-ye
- https://www.naukri.com/job-listings-principal-engineer-integration-architect-nagarro-hyder
- https://www.naukri.com/job-listings-principal-software-engineer-experience-vue-isolved-hcm

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Nagarro | Senior Staff Engineer, (CMDB,HAM,ITAM) | external_incomplete_or_timeout | company_ATS SmartRecruiters |
| GENZEON | Senior Technical Project Manager | apply_unconfirmed | Naukri |
| Accenture | Enterprise Solution Architect | ats_login_wall | company_ATS accenture.com/careers |
| Tiger Analytics | Snowflake + DBT Architect | apply_unconfirmed | Naukri |
| HighSpring India LLP | Technical Manager / Engineering Lead | apply_unconfirmed | Naukri |
| Tredence | Principal AWS Platform Architect | apply_unconfirmed | Naukri |
| Autorabit | Principal Engineer - 2026 | external_incomplete_or_timeout | company_ATS applytojob |
| TechnoGen | Engineering Manager | apply_unconfirmed | Naukri |
| Sutherland | CyberArk Architect | external_incomplete_or_timeout | company_ATS SmartRecruiters |
| Accenture | Enterprise Technology Architect | ats_login_wall | company_ATS accenture.com/careers |
| New Relic One | Principal Product Designer | external_incomplete_or_timeout | company_ATS Greenhouse |
| Medtronic | Principal Enterprise Software Engineer | external_incomplete_or_timeout | company_ATS Workday |
| Accenture | Packaged/SaaS App Engineering Lead | ats_login_wall | company_ATS accenture.com/careers |

## Notable skips
- Nagarro — Senior Staff Engineer, ServiceNow(CMDB,ITAM,SAM) — skip_title_keyword (ServiceNow form)
- Incedo-class CTC — skip_ctc_max_30 once
- Rapidue-class — hirist_login_required_skip (expected)
- Applied ≥8 on primary 1d/3d/7d — no 15/30/60 or extra-query expand
- Artifacts: `/opt/cursor/artifacts/naukri-profile-resume.json`, `/opt/cursor/artifacts/naukri-daily-apply.json`

## Code fix this run
- `tools/naukri/resume_and_filters.js` + `test_filters.js`: title-skip Fabric Architect (not Service Fabric), Apigee, Data Solution Architect, Xstore, AI Tech Lead, AEMaaCS/AEM, Vue-primary, CMDB/ITAM, Snowflake/DBT, CyberArk, Product Designer, Technical Project Manager, Testing Services, AWS Platform Architect
- Same-day follow-up: skip Wood Plc offshore piping/electrical/C&I and Engineering Manager-AI (Oracle Cloud ATS burn during age-expand re-run)

## Same-day post-fix re-run
- profileUpdated: **true** (re-upload `Rafi_Resume.docx`, Uploaded today; canonical restore at end)
- applied: **0** (did not re-submit; first-run jobs + false titles skipped)
- externalCompleted: **0**
- blocked: **3** — Knowbe4 Staff Engineer (Greenhouse timeout), WSA Solution Architect (company site timeout), Medtronic Senior Principal Enterprise Software Engineer (Workday timeout)
- skipped: 2099 · seen: 207 · early expand 3/7 · age expand 15/30/60 · extra .NET/Azure queries ran
- False titles now skip_title_keyword: Fabric Architect, Snowflake+DBT, Xstore, EM-AI, Wood offshore piping/electrical/C&I
- PR to main: branch `cursor/naukri-daily-2026-09-11-bbcf` pushed; GitHub createPullRequest was denied for this integration (owner must open/merge the registered PR)
