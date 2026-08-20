# Instahyre daily — 2026-08-20 (post-fix re-run)

Same-day `POST_FIX_RERUN=1` after merged [PR #220](https://github.com/rafi-solibri/MyRepo/pull/220) (`8a7f3e9` on `main`). Earlier morning run did not apply with that code; this session pulled `main` and executed `node tools/instahyre/daily_apply.js`.

## Summary
- Logged in: **yes** (CDP `sessionid`, opportunities page)
- Resume: `/workspace/resumes/Rafi_Resume.docx`
- Applied this session: **2** (interested **443 → 445**)
- Skipped: **668** · Blocked: **0** · Unique jobs seen: **670**
- Undecided opportunities: 3 (all non-Hyd: Sigmoid SA Bangalore; Bupa Head of Eng Gurgaon; DTDL Director Gurgaon)
- Path: Instahyre in-app (`candidate_opportunity/apply`). Spot-check UI: `application_sent` on both. No company-site ATS hrefs completed.

## Applied
1. **Coforge** — Data Architect (AWS) — Hyderabad — Instahyre (`oppId` 6186695015) — UI application_sent
2. **Marriott International** — Principal Engineer — Hyderabad — Instahyre (`oppId` 6186695074) — UI application_sent

Did not invent applies. Already-interested / already-applied API responses were skipped (88).

## Top skip reasons
- 545: location_not_hyd_remote
- 88: already_interested
- 23: generic_engineering_without_dotnet_cloud (React/Python/Java IC, generic fullstack)
- 5: pure_ai_data_without_dotnet (Azure/AWS Data Engineer titles)
- 4: java_primary
- 1 each: frontend_without_dotnet, qa_quality_engineering (SDET), wrong_stack_title (ServiceNow Technical Architect)

## Blocked
- None. No code-fixable helper failure. No second post-fix re-run launched (cap 5; this is re-run 1 for Instahyre today).

## Artifact
- `/opt/cursor/artifacts/instahyre-apply-report.json`
- `/opt/cursor/artifacts/instahyre-daily-run.json`
