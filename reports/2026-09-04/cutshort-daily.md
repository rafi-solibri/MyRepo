# Daily apply 2026-09-04

## Counts
- Scanned: **3345**
- Qualifying: **0**
- Applied: **0**
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 0 | locked-empty: **0** | verify-empty: 0
- Awaiting listed: 0 (final Q audit skipped — 0 applies this session)
- Failures (apply + locked-empty + verify-empty): **0**
- Tailored resumes: built **0** | profile uploaded **0** | upload failed 0
- Skip reasons: `{"skip_title":781,"location":237,"no_tier_match":43,"exp_max_low":1030,"ctc_under_35":1254}`

## Applied
_None_

## Failed applies
_None_

## Inventory (not invented)
Live CDP session was logged in (`Candidate dashboard` + Matches chrome). Newest `/findjobs/q` total **3374**. Hyd/remote Architect / Tech Lead / EM / Senior .NET/Azure cards that exist today all fail a hard skip:

- Listed max CTC **under 35L** (e.g. Cloud Architect 27L, Senior Azure Platform Engineer 30L, Senior .NET Developer 25L, several Tech Leads 15–18L)
- Title skip: SAP / Workday / data engineer / QA
- Bangalore-only / non-Hyd location
- Listed max exp **&lt; 6**

The 43 `no_tier_match` rows that passed Hyd/remote + exp≥6 + CTC≥35 were wrong-function titles (data scientist, PHP, sales, UX, ontologist, ServiceNow, MDM). Not applied.

## Code fix this run
- `/findjobs/q?matchesfor=` (lowercase) returns **0**. `matchesFor` is ignored and equals newest — dropped the dead 40-page wave.
- Skill `00115` is empty on `/findjobs/q` — omitted. Kept `.NET`/`C#`/`Azure`/`AWS`/`React`/`Java` skill waves.
- Daily markdown now prints `skipReasons` so a 0-qualifying day is inspectable.

## Profile
- Resume: `Rafi_Resume.docx` | Expected 65 LPA | Current 52 LPA | Hyd + Remote
- Artifact: `/opt/cursor/artifacts/` daily-run JSON from this session
