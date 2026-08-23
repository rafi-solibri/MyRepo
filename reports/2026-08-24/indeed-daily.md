# Indeed Daily — 2026-08-24 (post-fix re-run)

Same-day re-run on `main` after #245/#246 (Mohammed_Abdul_Rafi_Ahmed_Resume master refresh).
Earlier cron did not apply with the new resume. This agent used
`/workspace/resumes/Rafi_Resume.docx` (JD-tailored per job).

Two apply passes: first on merged resume, then again after the Sign In restore helper.

## Latest artifact (second pass)
`/opt/cursor/artifacts/indeed-daily-run.json` — **date 2026-08-24 IST**, source `cloud-warp-uc`, ok true

| Metric | Count |
| --- | ---: |
| Easy Apply submitted | 5 |
| External ATS confirmed | 1 |
| Rejected incomplete | 7 |
| Blocked | 17 |
| Skipped | 40 |
| Seen | 70 |

## Easy Apply submitted (second pass)
- **Genpact India Pvt. Ltd.** — Architect - Enterprise Application - Oracle N 4D — Hyderabad (`jk=6144ccb606d68e34`, also submitted on first pass)
- **Genpact India Pvt. Ltd.** — Senior Principal Consultant - Cloud Solution Architects — Hyderabad (`jk=88c15aca14c7f524`, recovered from first-pass bot-detection Sign In)
- **Genpact India Pvt. Ltd.** — Architect - Application Development Microsoft N 4D — Hyderabad
- **Experian** — Senior Software Engineer — Hyderabad
- **Emgage** — Solution Architect — Remote

## External ATS confirmed
- **NTT DATA** — Senior Application Architect — Hyderabad (confirmation)

## Also submitted on first pass (not re-counted above)
- **Genpact India Pvt. Ltd.** — Sr. Tech Lead - Application Development Microsoft N 4D — Hyderabad (`jk=175c17d4f70e64b4`)
- **NTT Ltd** — Senior Application Architect — Hyderabad (`jk=80e5e216f1e2be2f`, first listing)

## First pass snapshot
applied 2 / external 1 / rejected 4 / blocked 17 / skipped 35 / seen 59  
Late inventory hit `bot-detection-anonymous` Sign In hops; those were skipped as `title_not_target` before the helper fix.

## Notes
- Preflight: WARP+UC cleared CF (exit 0). Session restored via `secure.indeed.com/settings/account`.
- Resume tailor ran; upload filename stayed `Rafi_Resume.docx`.
- Helper fix on this branch: login wall / bot-detection before title skip; retry `continue2`; IST report date.
- PR create via `gh` was denied (`Resource not accessible by integration`); branch is pushed for owner merge.
