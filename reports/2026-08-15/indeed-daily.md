# Indeed daily — manual full run (IST today)

Morning cron and the #158 post-fix re-run did not leave usable same-day coverage on `main`. This run checked out `main`, did **not** set `FORCE_RESTORE_SESSIONS`, then ran preflight + `daily_apply.js` twice (second pass used the session-warm + form-fill helpers).

## Preflight
- `node tools/indeed/preflight.js` **exit 0** (`uc_bypass_cleared`, WARP SOCKS + UC Turnstile, filelock singleton)
- Chrome probe still saw Request Blocked; UC cleared CF
- Homepage after CF: anonymous **Get Started** despite valid Passport cookies
- Session warm via `secure.indeed.com/settings/account` restored Welcome

## Combined counts (not invented)
Two cloud WARP+UC passes. Unique Easy Apply submissions listed below (Centroid OCI appeared in both artifacts).

| Metric | Pass 1 | Pass 2 |
| --- | ---: | ---: |
| Submitted (Easy Apply) | 4 | 5 |
| External opened | 21 | 24 |
| Rejected incomplete | 14 | 11 |
| Blocked | 7 | 7 |
| Skipped | 33 | 44 |
| Seen | 79 | 90 |

Resume: `/workspace/resumes/Rafi_Resume.docx`

## Submitted (Easy Apply) — unique
- **Ampleopp Solutions** — Dynamics 365 CRM Senior Developer -Contract Role
- **Centroid Systems, Inc.** — OCI Cloud Architect – Contract to Hire role
- **Recruise** — AWS Solution Architect
- **QualMinds Technologies** — Software Engineer - C#.NET
- **Two95 International Inc.** — .Net Developer with PLANISWARE
- **Cidroy Infotech Pvt Ltd** — Senior Solution Architect (Remote)
- **Nagarro** — Senior Staff Engineer, .Net Fullstack (Remote)
- **Nagarro** — Senior Engineer, .Net Web (Remote)

## Blocked (pass 2)
- 6× `easy_apply_recaptcha` (Nagarro×3, OpenLake, Worklio, CogniCor)
- 1× `search_blocked`

## Rejected
SmartApply employer questions still incomplete on several listings (custom dropdowns / reason-for-change). Filler patches landed on the branch during the run.

## Skipped (pass 2)
- title_not_target 34, location 7, no_apply_button 2, title_skip 1

## Code fixes (feature branch)
- Passport warm after Turnstile + Local State copy
- SmartApply DOB; skip PAN/Aadhaar invent
- Full name mapping; custom education/years comboboxes
- FTE vs contract + numeric hourly rate
- Reason-for-change one-liner

PR create from this environment needs owner approval (`gh` GraphQL createPullRequest denied). Branch: `cursor/indeed-daily-*-f01b`.
