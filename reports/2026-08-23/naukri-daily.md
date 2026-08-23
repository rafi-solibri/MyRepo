# Naukri Daily — 2026-08-23 (post-fix re-run #2, PR #244)

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` (owner master `Mohammed_Abdul_Rafi_Ahmed_Resume.docx` via #244) | Expected 65 LPA / Current 52 LPA | Hyd + Remote

This run pulled `main` at `df7b068` (#244) and executed `node tools/naukri/daily_apply.js` so today's applies used the merged resume. Earlier today: morning cron `bc-a036f2ba` (0 applies, merged #241) and post-fix #1 `bc-97475405` (0 applies on #241, before #244).

Agent: https://cursor.com/agents/bc-29187929-fd55-4768-99b3-20bdfc6705be  
Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441  
`POST_FIX_RERUN=1` · re-run 2 / 5 for 2026-08-23 IST

## STEP 0 — Profile resume refresh
- **profileUpdated:** `true` (attempt 1)
- **resume path:** `/workspace/resumes/Rafi_Resume.docx`
- **Naukri label:** Mohammed_Abdul_Rafi_Ahmed_Resume.docx / Uploaded today (`todayHit: true`)
- **headline soft-touch:** skipped (`headline_input_missing`)
- **canonical restore at end:** `ok: true` → `Rafi_Resume.docx`
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts
- profileUpdated: **true**
- applied: **2** (tailoredApplies: 2)
- externalCompleted: **0**
- blocked: **0**
- skipped: **2604** (seen 210)
- earlyExpandedAges: `[3, 7]` (applied 2 &lt; 3 after age 1)
- expandedAges: `[15, 30, 60]`
- extraQueries: `.net azure architect` · `solution architect azure` · `dotnet engineering manager` · `principal software engineer .net` · `technical architect c#` · `cloud architect .net`

## Applied (helper-confirmed — not invented)

| Company | Role | Location | Path | Resume | Confirm |
| --- | --- | --- | --- | --- | --- |
| Tata Consultancy Services | Microfocus Rehost Technical Architect (7 locations) | Hyderabad, Chennai, Bengaluru | Naukri chatbot | tailored `Rafi_Resume.docx` | `chatbot:responses_thanks` |
| Cotiviti | Technical Lead - Full Stack (React + Node JS + AWS) | Hybrid - Hyderabad | Naukri | tailored `Rafi_Resume.docx` | `view_applied_jobs` |

Job URLs:
- TCS: https://www.naukri.com/job-listings-microfocus-rehost-technical-architect-7-locations-tata-consultancy-services-hyderabad-chennai-bengaluru-12-to-18-years-230826003146?src=directSearch
- Cotiviti: https://www.naukri.com/job-listings-technical-lead-full-stack-react-node-js-aws-cotiviti-hyderabad-10-to-14-years-230826004057?src=directSearch

Both are **wrong-stack false applies** (mainframe rehost / React+Node primary). Logged as submitted because the helper confirmed them; filters did not skip the titles. Durable skip added in this PR.

## Already-applied (skipped, not re-applied)
- Clean Harbors | .Net Fullstack Tech Lead | `already_applied_detail`
- Globallogic Senior Architect | skipped via #241 `skip_jd_non_dotnet` / Applied CTA (morning false-apply)

## Hirist skips (not hard-blocked)
- Epam Systems | Full Stack Solution Architect Node.js/AngularJS
- Anlage Infotech | Full Stack AI Manager
- Mancer Consulting Services | Engineering Manager - Platform

## Skip reasons (top)
- duplicate_in_run: 2378
- skip_title_keyword: 143
- skip_no_dotnet: 34
- skip_seniority: 28
- skip_location: 7
- skip_company: 4
- skip_ctc_max_30: 4
- hirist_login_required_skip: 3
- skip_jd_non_dotnet_detail: 1 (Canterr Inc Staff Engineer)
- skip_ctc_max_32.5: 1
- already_applied_detail: 1

## Code fix (this PR)
- `SKIP_TITLE_RE`: `microfocus` / `micro focus` / `rehost`
- `NON_DOTNET_PRIMARY_RE`: `node.js` / `node js` (still allows `.NET + Node.js` on the title)
- Tests in `tools/naukri/test_filters.js`

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/workspace/artifacts/naukri-daily-apply.json` (gitignored mirror)
