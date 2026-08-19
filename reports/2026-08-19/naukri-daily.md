# Naukri daily — 2026-08-19 (cloud)

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` | Expected 65 LPA / Current 52 LPA | Hyd + Remote

## STEP 0 — Profile resume refresh
- **ok:** yes (`profileUpdated: true`)
- Resume filename shown: **Rafi_Resume.docx**
- Verify: `todayHit: true`, matchedToken `today`, line `Rafi_Resume.docx` / `Uploaded today`
- Headline soft-touch: skipped (`headline_input_missing`) — file upload alone advanced “Updated today”
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts
- profileUpdated: **true**
- applied: **2**
- externalCompleted: **0**
- blocked: **2**
- skipped: **2791** (seen 191)
- earlyExpandedAges: `[3, 7]`
- expandedAges: `[15, 30, 60]`

## Applied
- Hiring for a Miscellaneous company (Lecan Solutions) — Technical Lead — Hyderabad, Chennai, Bengaluru — Naukri chatbot (`responses_thanks`) — `Rafi_Resume.docx` — https://www.naukri.com/job-listings-technical-lead-lecan-solutions-hyderabad-chennai-bengaluru-5-to-12-years-190826011460
- Solugenix — Lead Full stack Engineer - Azure — Hyderabad, Indore, Bengaluru — Naukri chatbot (`responses_thanks`) — `Rafi_Resume.docx` — https://www.naukri.com/job-listings-lead-full-stack-engineer-azure-solugenix-indore-hyderabad-bengaluru-10-to-20-years-180826013658

## Blocked
- Tata Consultancy Services — Power Bi Architect — `apply_unconfirmed` / `no_chat` (false-attempt; Architect waiver). Filter fix: skip Power BI / BI Architect titles.
- Principal Financial Group — Associate Director - Engineering — `apply_unconfirmed` / `chat_steps_exhausted` (repeat chatbot wall; not counted as applied)

## Already applied (not re-counted)
- i2e Consulting — Solution Architect (Remote) — CTA Applied
- Clean Harbors — .Net Fullstack Tech Lead (Hyderabad) — CTA Applied

## Hirist (skipped, not hard-blocked)
- ValGenesis — Software Engineering Manager — Full Stack
- Anlage Infotech — Full Stack AI Manager
- Rapidue Technologies — Solution Architect - Full Stack
- Mancer Consulting Services — Engineering Manager - Platform

## Code fix this run
- Branch: `cursor/naukri-daily-2026-08-19-fda2` (pushed)
- `tools/naukri/resume_and_filters.js`: `SKIP_TITLE_RE` now matches `power bi` / `powerbi` / `bi architect` so the Architect/Lead waiver does not Quick-Apply BI-only titles.
- PR create blocked (`gh` 403 Resource not accessible by integration; ManagePullRequest waiting on user approval) — branch ready for owner merge + `bash scripts/auto-merge-fix-pr.sh`

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
