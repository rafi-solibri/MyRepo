# Indeed daily — manual full run (IST today)

Morning cron (`bc-5b4f5e6c`) and the #158 post-fix re-run (`bc-90bf2c55`) did not leave usable same-day coverage on `main`. This run checked out `main`, did **not** set `FORCE_RESTORE_SESSIONS`, then ran preflight + `daily_apply.js`.

## Preflight
- `node tools/indeed/preflight.js` **exit 0** (`uc_bypass_cleared`, WARP SOCKS + UC Turnstile, filelock singleton)
- Chrome probe still saw Request Blocked; UC cleared CF
- Homepage after CF: anonymous **Get Started** despite valid Passport cookies
- Session warm via `secure.indeed.com/settings/account` restored Welcome (`sessionWarmedVia`)

## Counts (cloud WARP+UC, not invented)
| Metric | Count |
| --- | ---: |
| Submitted (Easy Apply) | **4** |
| External opened (company site) | 21 |
| Rejected incomplete | 14 |
| Blocked | 7 |
| Skipped | 33 |
| Seen | 79 |

Resume: `/workspace/resumes/Rafi_Resume.docx`

## Submitted (Easy Apply)
- **Ampleopp Solutions** — Dynamics 365 CRM Senior Developer -Contract Role
- **Centroid Systems, Inc.** — OCI Cloud Architect – Contract to Hire role
- **Recruise** — AWS Solution Architect
- **QualMinds Technologies** — Software Engineer - C#.NET

## Blocked
- 6× `easy_apply_recaptcha` (Cidroy, Loti AI, Nagarro×2, Pivotree, CENTROID duplicate)
- 1× `search_blocked`

## Rejected (Easy Apply incomplete)
Mostly custom SmartApply dropdowns / leftover Yes on numeric fields (education, years, rate/hr, full name). Follow-up filler commits on this branch were not loaded by the already-running apply process.

## Skipped
- title_not_target 28, no_apply_button 2, title_skip 2, location 1

## Code fixes (feature branch, ready PR pending environment approval)
- Passport warm after Turnstile + Local State copy
- SmartApply DOB `16/01/1989`; skip PAN/Aadhaar invent
- Full name mapping; custom education/years comboboxes
- FTE vs contract + numeric hourly rate; require how-many-years before numeric experience

## vs earlier same-day runs
| Run | Applied | Seen | Usable on main? |
| --- | ---: | ---: | --- |
| Morning cron | 0 | 0 | No (false login_required) |
| Post-fix #158 re-run | 5 | 78 | No (fixes never merged) |
| This manual run | 4 | 79 | Yes (real Easy Apply + report) |
