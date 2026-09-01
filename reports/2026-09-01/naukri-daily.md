# Naukri daily — 2026-09-01 (post-fix re-run #2)

Ran on `main` at `6c3961b` (`#305` LinkedIn password isolation + `#304` Naukri title skips). `POST_FIX_RERUN=1`. This is same-day re-run **2/5**.

## Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied: **1**
- externalCompleted: **0**
- blocked: **2**
- skipped: 3162 (2941 duplicate_in_run) · seen: 206 · tailoredApplies: 1

## Profile resume refresh (STEP 0)
- ok: true · profileUpdated: true · matchedToken: **Uploaded today** · updateOn: *(empty)*
- resume filename shown: `Rafi_Resume.docx`
- path: toptier-filechooser (`div.my-10 button:has-text('Update')`)
- headline soft-touch: failed (`headline_input_missing`) — same as morning / re-run 1; not a new blocker
- profile restored to canonical `Rafi_Resume.docx` at end of run

## Applied
| Company | Role | Path | Resume |
| --- | --- | --- | --- |
| Tata Consultancy Services | Azure Infra Architect - S | Naukri Quick Apply (`chatbot:responses_thanks`) | tailored `/tmp/naukri-tailored/640f027df171/Rafi_Resume.docx` |

- URL: https://www.naukri.com/job-listings-azure-infra-architect-s-tata-consultancy-services-hyderabad-chennai-bengaluru-10-to-15-years-280826006118?src=directSearch
- Location: Hyderabad, Chennai, Bengaluru · query: `solution architect azure` · age: 15d
- **False-fit** — Azure *infra* architect (parity with AWS/GCP/Cloud Infra already skipped). Filter fix in this PR.

## Blocked (not counted as applied)
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Blackbaud | Software Engineer, Principal - .NET DevOps | `ats_login_wall` (owner Workday login) | company_ATS Workday |
| Optum | Senior Azure Cloud Architect | `external_incomplete_or_timeout` | company_ATS UHG careers |

- Blackbaud: https://blackbaud.wd1.myworkdayjobs.com/en-US/ExternalCareers/job/Hyderabad---India-(Skyview)/Software-Engineer--Principal---NET-DevOps_R0014448/apply/autofillWithResume
- Optum: https://careers.unitedhealthgroup.com/job/hyderabad/senior-azure-cloud-architect/34088/98871265200

Same two walls as re-run 1 — not new code-fixable blockers.

## Already applied today (skipped)
- Clean Harbors — .Net TEchnical Architect — `already_applied_detail`
- Sidgs Digisol — Apigee Architect — `already_applied_detail`
- Morning + re-run 1 submits (17 Naukri Quick Applies) were not re-submitted. #304 title-skips held: Cisco ASIC DFT, Oracle Fusion / Oracle HCM, IMDS-class titles.

## Expand
- Age 1: 0 applies → early expand 3,7 → still thin → expand 15/30/60 + extra .NET/Azure queries + recommended/homepage
- Hirist: SKIP (no dest auth) — not a hard block

## Code fix this run
- `tools/naukri/resume_and_filters.js`: title-skip `azure infra(structure)? architect` (SKIP_TITLE with aws; PURE_AI_DATA with aws/gcp/cloud). `Azure Architect .NET` still applies.
- `tools/naukri/test_filters.js`: coverage for TCS-style `Azure Infra Architect - S`

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-daily-apply-20260901-postfix2.log`
- `reports/2026-09-01/naukri-daily.json`
