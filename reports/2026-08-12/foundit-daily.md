# Foundit daily 2026-08-12

## Counts
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT JWT OK)
- Applied tab: **458 → 459** (+1 this run; earlier same-day run was 455→458)
- Intentional applies (this run): **1**
- Duplicates (`userJobInfo` / Falcon): **35**
- Skipped: **508** (location ~183 / no .NET 150 / no seniority 110 / exp 46 / CTC 10 / other)
- Blocked (Foundit): **0**
- Age window used: **3650d** (expanded after thin fresh Hyd/remote senior .NET inventory)
- Resume: `resumes/Rafi_Resume.docx` (52 → 65 LPA)
- Artifact: `/opt/cursor/artifacts/foundit-daily-run.json`
- No `canJobApply` calls

## Applied (this run)
1. Aveva — Senior Consultant - System Platform — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` (200) → Workday Hyderabad `R014980` — Falcon registered on Foundit; Workday stopped at **Create Account/Sign In** (`ats_login_wall`, owner)

## Blocked / owner
- Aveva Workday account wall after Apply Manually (evidence: `/opt/cursor/artifacts/foundit-aveva-ats.json`)
- Remaining eligible Hyd/remote senior .NET inventory exhausted (duplicates) after age expand

## Code fixes (branch `cursor/foundit-fix-seniority-c8ce`)
- `filters.js` `hasSeniority`: accept `\bsenior\b` / `\bsr.?` (fixes `.Net Senior Developer` / `Senior Backend Developer (.NET)` false skips) + tests
- `daily_apply.js` ATS: Workday Apply → Apply Manually + Next/Submit; detect Create Account/Sign In as login wall
- Logged in `automation-prompts/ISSUES_AND_FIXES.md`
- **PR:** push OK; `gh pr create` / REST returned **403 Resource not accessible by integration** (token cannot open PRs). Ready for parent/owner: open PR from branch → `bash scripts/auto-merge-fix-pr.sh`

## Top LinkedIn referral drafts
1. Aveva / Senior Consultant - System Platform — ask for HM referral; 52→65 LPA, immediate, Rafi_Resume.docx
