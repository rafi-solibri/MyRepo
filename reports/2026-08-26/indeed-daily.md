# Indeed Daily — 2026-08-26 (post-fix re-run)

Same-day re-run on merged `main` (#270 hitechcity ATS Gmail OTP abort) plus a **new** Indeed SmartApply resume-upload fix. Morning automation (`bc-0bdfe17c`) cleared CF/login but submitted **0** (resume-selection: *We could not upload your resume file*). This re-run applied with a Chrome-printed PDF fallback.

Preflight: **EXIT=0** (`uc_bypass_cleared`). Session restored via `https://secure.indeed.com/settings/account`. Resume: `resumes/Rafi_Resume.docx` (from owner master) + `Rafi_Resume.pdf`. No invented applies.

## Counts
- **Submitted (Easy Apply):** 2
- **External completed:** 0
- **Rejected incomplete:** 3
- **Blocked:** 23
- **Skipped:** 55
- **Seen:** 82
- **ok:** True
- **finishedAt:** 2026-08-26T05:45:14Z

### vs morning automation (still 0 submitted)
| Metric | Morning (`bc-0bdfe17c`) | This re-run |
| --- | ---: | ---: |
| Applied | 0 | **2** |
| External | 0 | 0 |
| Rejected | 6 | 3 |
| Blocked | 24 | 23 |
| Skipped | 45 | 55 |
| Seen | 75 | 82 |

## Applied (Easy Apply, confirmed)
- **Genpact India Pvt. Ltd.** — Technical Architect 4D — Hyderabad (`jk=5b3976f0d15303ce`) — PDF `Rafi_Resume.pdf` uploaded just now after three DOCX rejects
- **Websenor** — Senior .Net FSE — Remote (`jk=e1aff87874360a35`)

## Rejected (incomplete, not counted as applied)
- **ValGenesis** — Senior Software Engineer, Fullstack — stuck on employer **questions** (resume step passed)
- **LTIMindtree** — Senior Principal - Architecture — stuck on employer **questions** (resume step passed)
- **CoverGo** — Solutions Architect (Insurance) Fully Remote — stuck on employer **questions** (location city/state)

## Blocked (not invented)
- `no_ats_form` 8 — company sites without a completable apply form
- `external_incomplete_or_timeout` 8 — ATS fill timed out
- SOCKS `ERR_SOCKS_CONNECTION_FAILED` 6 — employer hosts via WARP
- `search_blocked` 1 — brief CF on SERP (run continued)

## Skipped
- `already_applied` 25 (prior days + today’s 2)
- `title_not_target` 21
- `location` 6
- `title_skip` 2
- `no_apply_button` 1

## Fix landed (this branch; merge to main)
SmartApply rejected font-stripped 20KB DOCX (and the 3.9MB owner master). PDF fallback succeeded. Helpers: `upload_smartapply_resume`, skip upload on job-view pages, prefer PDF first.

## Artifacts
- `/opt/cursor/artifacts/indeed-daily-run.json`
- `/opt/cursor/artifacts/indeed-apply-report.json`
- `/opt/cursor/artifacts/indeed-preflight.json`
- `reports/2026-08-26/indeed-daily.md`
