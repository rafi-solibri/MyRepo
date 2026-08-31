# Naukri daily — 2026-08-31

## Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied: **1**
- externalCompleted: **0**
- blocked: **1**
- skipped: 2737 (dup-heavy) · seen: 182 · tailoredApplies: 1

## Profile resume refresh
- ok: true · matchedToken: Uploaded today · resume: Rafi_Resume.docx
- path: toptier-filechooser `#attachCV` / Update

## Applied
| Company | Role | Path | Resume |
| --- | --- | --- | --- |
| Accion Labs | Technical Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored `/tmp/naukri-tailored/0c37417e0fc6/Rafi_Resume.docx` |

- URL: https://www.naukri.com/job-listings-technical-architect-accion-labs-hyderabad-pune-bengaluru-12-to-18-years-310826001109?src=directSearch
- Location: Hyderabad, Pune, Bengaluru · query: dotnet architect · age: 1d

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Blackbaud | Software Engineer, Principal - .NET DevOps | ats_password_policy (Create Account abort; no Sign In fallback) | company_ATS Workday |

- https://blackbaud.wd1.myworkdayjobs.com/en-US/ExternalCareers/job/Hyderabad---India-(Skyview)/Software-Engineer--Principal---NET-DevOps_R0014448/apply/autofillWithResume

## Notable skips
- Clean Harbors — .Net TEchnical Architect — already_applied_detail
- Incedo — .Net Lead — skip_ctc_max_30 (<35 LPA floor)
- Leading Client — .NET Full Stack Developer — skip_seniority
- Rapidue — Solution Architect — hirist_login_required_skip (expected)
- Thin .NET title inventory today (4 .NET titles in 182 seen); early+age+extra query expand ran

## Code fix this run
- `tools/naukri/workday_apply.js`: Create Account `ats_password_policy` / login_wall now falls through to Sign In; `authFailureReason` ignores static Password Requirements checklist; `test_workday_auth.js` added
