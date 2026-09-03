# Naukri daily — 2026-09-03 (post-fix re-run)

Ran on `main` @ `2a054d7` (merged #318 Oracle APEX / NetSuite / DevOps CoE / Accenture fail-fast).
`POST_FIX_RERUN=1`. This session executed STEP 0 + applies with the merged code.

## Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied: **1**
- externalCompleted: **0**
- blocked: **1**
- skipped: 3240 (dup-heavy) · seen: 209 · tailoredApplies: 1 · queriesRun: 288
- early expand ages 3/7 (applied 1 < 3) then 15/30/60 + extra queries (applied 1 < 8)

## Profile resume refresh
- ok: true · matchedToken: Uploaded today · resume: Rafi_Resume.docx
- path: toptier-filechooser `#attachCV` / Update
- profile restored to canonical CV at end of run

## Applied
| Company | Role | Path | Resume |
| --- | --- | --- | --- |
| Axiscades Engineering Technologies | Technical Lead - Test Engineer | Naukri Quick Apply (chatbot:responses_thanks) | tailored `/tmp/naukri-tailored/a7ba9c12bb2d/Rafi_Resume.docx` |

- URL: https://www.naukri.com/job-listings-technical-lead-test-engineer-axiscades-engineering-technologies-hyderabad-chennai-bengaluru-8-to-13-years-020926034381?src=directSearch
- Location: Hybrid - Hyderabad, Chennai, Bengaluru · query: technical lead · age: 1d
- **False apply** — QA/test title; title-skip added this run (does not un-apply)

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Amgen Inc | Director, Commercial Analytics - Obesity | external_incomplete_or_timeout | company_ATS careers.amgen.com |

- https://careers.amgen.com/en/job/-/-/87/97172584080?source=rd_naukri
- **False ATS attempt** — pharma commercial analytics; title-skip added this run

## Notable skips
- Clean Harbors — .Net TEchnical Architect — already_applied_detail
- Sidgs Digisol — Apigee Architect — already_applied_detail
- Incedo — .Net Lead role- Immediate joiner — skip_ctc_max_30
- Blackbaud — Software Engineer, Principal - .NET DevOps — skip_title_keyword (DevOps; #318)
- TCS / ICICI-style .NET developer titles — skip_seniority
- Thin .NET title inventory (7 .NET-ish in 209 seen)

## Code fix this run
- `tools/naukri/resume_and_filters.js`: skip `test engineer` / `test lead` / `qa lead` and `commercial analytics`
