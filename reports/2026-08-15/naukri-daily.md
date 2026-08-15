# Naukri daily — 2026-08-15 (post-fix re-run on #162)

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` | Expected 65 LPA / Current 52 LPA | Hyd + Remote

Ran on merged `2140d75` (`fix(ats): submit company-site applies instead of timing out on hops` #162), then a same-session filter/confirm follow-up.

## STEP 0 — Profile resume refresh
- **profileUpdated:** true
- **verify:** Rafi_Resume.docx / Uploaded today
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts
- profileUpdated: **true**
- applied: **2** (not invented)
- externalCompleted: **0**
- blocked: **4**
- skipped: 3042 (seen 199)
- already applied today (skipped): i2e Consulting Solution Architect; Clean Harbors .Net Fullstack Tech Lead

## Applied
- 99yellow — Chief Technology Officer — Hyderabad — Naukri chatbot (`responses_thanks`) — `Rafi_Resume.docx` — https://www.naukri.com/job-listings-chief-technology-officer-99yellow-hyderabad-12-to-20-years-290726017151?src=drecomm_aurus
- Meltwater — Manager, SW Engineering — Hyderabad — Naukri Quick Apply — confirmation widget **View applied jobs (20+)** (first logged `apply_unconfirmed`; confirmer now treats that widget as success) — `Rafi_Resume.docx` — https://www.naukri.com/job-listings-manager-sw-engineering-meltwater-hyderabad-8-to-13-years-010726500584?src=directSearch

## Blocked
- Mihira Ai — Manager, SW Engineering — `external_incomplete_or_timeout` — https://mihira.ai/careers.html (brochure careers page, no ATS form)
- Principal Financial Group — Associate Director - Engineering — `apply_unconfirmed` (CTA stayed Quick apply; `chat_steps_exhausted`)
- Vanguard — Senior Specialist CTO AI Ready Data/DTR — `external_link_not_opened` (product-string CTO; filter tightened so this is no longer arch/lead)
- i2e Consulting — Solution Architect — `quick_apply_not_found` (already applied earlier today)

## Code fix
- Branch: `cursor/naukri-daily-post-fix-re-run-2026-08-15-4e2d`
- `ARCH_LEAD_RE`: `Manager, SW Engineering` + `Chief Technology Officer` (bare `CTO` only; not “Specialist CTO AI”)
- `confirmApplied`: visible **View applied jobs** counts as success
- Filter tests updated

## Artifacts
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-run.json`
