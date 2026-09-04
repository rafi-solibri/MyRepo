# Hirist daily — 2026-09-04 (post-fix re-run)

## Status
Ran on **merged `#321`** (`c7a59b3` DFT/VLSI HARD-skip) with `POST_FIX_RERUN=1`. Preflight + CDP login OK (`hirist_seeker_enc`). Resume: `resumes/Rafi_Resume.docx`.

## This re-run (merged code)
| Path | Count |
| --- | --- |
| In-app applied | **0** (none invented) |
| External ATS | **0** |
| Rejected | **1** — 1667999 Full Stack Developer - .Net/AngularJS @ DIgitalcubez — `assessment_required` |
| Blocked | **0** |
| Skipped / seen | 442 / 443 |

Hirist `POST /job/apply-multiple` returned HTTP 200 with `[{ success: false, message: "Assessment/ screening is required to apply for this Job" }]`. The old runner counted that as applied. Job is **not** on `/job/applied-jobs`.

## Already on Hirist today (earlier 03:32 IST run, before #321)
These are live on `/job/applied-jobs` — skipped if they reappear:

- 1668422 — Technical Lead - .NET/Azure — Tidyhire
- 1668444 — Solution Architect - API/.Net — sugandi consultancy
- 1668162 — Principal Engineer - Banking/Fintech Platform — Watson Search Partners
- 1668350 — DFT Architect — Watson Search Partners (**pre-fix false stack**; HARD-skipped after #321)
- 1665372 — .Net Integration Specialist - C# Programming — sugandi consultancy
- 1668325 — Software Engineer - .Net/React.js — Kimoha Technologies

Morning transcript also listed 1667999 as applied — **incorrect**; assessment wall, not submitted.

## Filters
- DFT / SystemVerilog / UVM titles → `wrong_stack_title` (merged #321).
- 254 IDs loaded from `/job/applied-jobs` and skipped.

## Code fix (this run)
`tools/hirist/apply_result.js` — parse apply-multiple array `success`; skip applied-jobs IDs; confirm land before counting. Branch `cursor/hirist-daily-post-fix-re-run-2026-09-04-5387`.

## Artifacts
- `/opt/cursor/artifacts/hirist-apply-report.json`
- `/opt/cursor/artifacts/hirist-daily-run.json`
