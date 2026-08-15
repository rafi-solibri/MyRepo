# Indeed daily — 2026-08-15 (post-fix re-run on #162)

## Status
**Ran on merged `2140d75` (#162 ATS hops) plus local Passport-warm / SmartApply fills.**
Preflight WARP+UC exited 0. Resume: `/workspace/resumes/Rafi_Resume.docx`.
No invented applies. Already-submitted listings were left to Indeed's own already-applied text.

## Totals (this cloud session, usable pass)
Source: `cloud-warp-uc` · warmed via `secure.indeed.com/settings/account`

| Metric | Count |
| --- | ---: |
| Easy Apply submitted | **3** |
| Company-site ATS completed | **0** |
| Easy Apply incomplete | 2 |
| Blocked | 9 |
| Skipped | 16 |
| Seen | 30 |

## Submitted (Easy Apply)
- Frontline Data Solutions — Engineering Manager (Hyd) `jk=adfd39278dc474e5`
- WonderBotz — Senior Consultant Program Manager - Tungsten (Hyd) `jk=78170ea0073881fd`
- Innovapptive — Solution Architect (Hyd) `jk=078ea7a80e897f43`

## Rejected / incomplete
- Cognizant Principal Architect — Easy Apply flipped to company careers page, incomplete
- ValGenesis Senior Software Engineer, Fullstack — SmartApply stuck on "India - Standard"

## Blocked
- 7× `external_incomplete_or_timeout` (Cognizant, BytesEdge, Absyz, QualiZeal, Infovity, CGLIA, Arcesium Greenhouse) — #162 followed hops off Indeed; employer ATS did not confirm in the time cap
- 1× `search_blocked` (Engineering Manager .NET / Hyd)
- 1× `easy_apply_recaptcha` (Techblocks .NET Fullstack Developer)

## Skipped
- 15× `title_not_target` (PM / Dev Manager / Integration Developer / junior-mid Fullstack, etc.)
- 1× `no_apply_button`

## First pass on #162 only (before warmup)
Homepage stayed anonymous **Get Started** after Turnstile despite valid Passport cookies → false `indeed_login_required`, 0 seen. Same seed restored Welcome after settings warmup (already proven on the morning unmerged branch).

## Code on this branch (not yet on `main` — `gh createPullRequest` denied)
- `warm_passport_session()` + copy `Local State` into the hybrid UC profile
- SmartApply: full name, years/education comboboxes, FTE/rate/reason-for-change, certify, start date
- `/tel/` no longer matches "tell us" (unique pitch was getting the phone number)
- Title/salutation → Mr.

Branch: `cursor/indeed-daily-post-fix-re-run-2026-08-15-d76e`
Open PR: https://github.com/rafi-solibri/MyRepo/pull/new/cursor/indeed-daily-post-fix-re-run-2026-08-15-d76e

## Artifacts
- `/opt/cursor/artifacts/indeed-daily-run.json`
- `/opt/cursor/artifacts/indeed-apply-report.json`
- `/opt/cursor/artifacts/indeed-preflight.json`
