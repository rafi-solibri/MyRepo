# Hirist daily — 2026-09-04 (post-fix re-run #2)

## Status
Ran on **merged `main` `a385176`** (`#321` DFT/VLSI HARD-skip + `#323` Naukri, unrelated) with `POST_FIX_RERUN=1`. Preflight + CDP login OK (`hirist_seeker_enc` on `/applied-jobs`). Resume: `resumes/Rafi_Resume.docx`.

Parser from the earlier re-run (`apply_result.js`) was cherry-picked locally so HTTP 200 + `success:false` is **not** counted as applied.

## This re-run (merged code + parser)
| Path | Count |
| --- | --- |
| In-app applied | **0** (none invented) |
| External ATS | **0** |
| Rejected | **1** — 1667999 Full Stack Developer - .Net/AngularJS @ DIgitalcubez — `assessment_required` |
| Blocked | **0** |
| Skipped / seen | 445 / 446 |

Eligible Hyd/.NET inventory is exhausted. The only remaining candidate (1667999) is assessment-walled and is **not** on `/job/applied-jobs`. 254 already-applied IDs were loaded and skipped.

## Already on Hirist today (03:32 UTC run, before #321)
Live on `/job/applied-jobs` — skipped if they reappear:

- 1668422 — Technical Lead - .NET/Azure — Tidyhire
- 1668444 — Solution Architect - API/.Net — sugandi consultancy
- 1668162 — Principal Engineer - Banking/Fintech Platform — Watson Search Partners
- 1668350 — DFT Architect — Watson Search Partners (**pre-#321 false stack**; HARD-skipped after #321)
- 1665372 — .Net Integration Specialist - C# Programming — sugandi consultancy
- 1668325 — Software Engineer - .Net/React.js — Kimoha Technologies

Morning transcript also listed 1667999 as applied — **incorrect**; assessment wall, not submitted.

## Filters
- DFT / SystemVerilog / UVM titles → `wrong_stack_title` (merged #321). Confirmed e.g. SOC/IP SystemVerilog/UVM skipped.
- Skip-reason mix this run: location_not_hyd_remote 261, pure_ai_data_without_dotnet 68, wrong_stack_title 38, java_primary 34, plus smaller buckets.

## Code fix (this run)
`tools/hirist/apply_result.js` — parse apply-multiple array `success`; skip `/job/applied-jobs` IDs; confirm land before counting. Branch `cursor/hirist-daily-post-fix-re-run-2026-09-04-4c40`. `gh pr create` is blocked (integration permissions); earlier re-run hit the same wall.

Did **not** launch another same-day cloud re-run (already 2 of 5; this session already executed the job with the fix).

## Artifacts
- `/opt/cursor/artifacts/hirist-apply-report.json`
- `/opt/cursor/artifacts/hirist-daily-run.json`
