# Naukri daily — 2026-09-02

## Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied: **1**
- externalCompleted: **0**
- blocked: **1**
- skipped: 3240 (dup-heavy) · seen: 198 · tailoredApplies: 1

## Profile resume refresh
- ok: true · profileUpdated: true · matchedToken: Uploaded today · resume: Rafi_Resume.docx
- path: toptier-filechooser `#attachCV` / Update (attempt 1)
- master rebuilt: Mohammed_Abdul_Rafi_Ahmed_Resume.docx (3.9MB) → Rafi_Resume.docx (20945B)
- profile restored to canonical CV at end of run

## Applied
| Company | Role | Path | Resume |
| --- | --- | --- | --- |
| Arcesium | Forward Deployed Solution Architect (FDSA) | Naukri Quick Apply (chatbot:responses_thanks) | tailored `/tmp/naukri-tailored/1a2e3447f552/Rafi_Resume.docx` |

- URL: https://www.naukri.com/job-listings-forward-deployed-solution-architect-fdsa-arcesium-hyderabad-10-to-15-years-020926009338?src=directSearch
- Location: Hyderabad · query: solution architect · age: 1d
- Architect-title apply (Hyd). Chatbot confirmed. Recruiter note not sent.

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Blackbaud | Software Engineer, Principal - .NET DevOps | ats_login_wall (Workday Sign In stayed on auth; `NAUKRI_WORKDAY_PASSWORD` present) | company_ATS Workday |

- https://blackbaud.wd1.myworkdayjobs.com/en-US/ExternalCareers/job/Hyderabad---India-(Skyview)/Software-Engineer--Principal---NET-DevOps_R0014448/apply/autofillWithResume
- Owner action: complete Blackbaud Workday Sign In once (headed) or confirm tenant password. Not treated as a same-day code fix (login wall after helper exists).

## Notable skips
- Clean Harbors — .Net TEchnical Architect — already_applied_detail
- Sidgs Digisol — Apigee Architect — already_applied_detail
- Incedo — .Net Lead role- Immediate joiner — skip_ctc_max_30 (<35 LPA floor)
- Leading Client — .NET Full Stack Developer — skip_seniority
- Defence & Aerospace — Senior Full Stack Developer - .Net & Vue/Angular — skip_seniority
- Salesforce / Cadence — skip_company
- Thin .NET title inventory today (Clean Harbors already applied, Incedo 30 LPA, Blackbaud Workday wall, one IC .NET fullstack). Early age 3/7 + ages 15/30/60 + extra .NET/Azure queries + recommended/homepage ran.

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
