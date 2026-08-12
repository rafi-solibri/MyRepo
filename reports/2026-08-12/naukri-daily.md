# Naukri Daily — 2026-08-12

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` | Expected 65 LPA / Current 52 LPA | Hyd + Remote

## STEP 0 — Profile resume refresh
- **profileUpdated:** `True`
- **verify:** Resume / Update /  / Rafi_Resume.docx /  / Uploaded today
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts
- profileUpdated: **True**
- applied: **0**
- externalCompleted: **0**
- blocked: **1**
- skipped: **2483** (seen 301)
- expandedAges: `[15, 30]`

## Applied / External
_None confirmed this run (no invented applies)._

## Blocked
- Apple | SRE Engineering Manager | `ats_login_or_captcha` | https://jobs.apple.com/en-in/details/200657773-1052/sre-engineering-manager?team=SFTWR

## Skip reasons (top)
- duplicate_in_run: 2179
- already_applied_detail: 156
- skip_title_keyword: 75
- skip_seniority: 36
- skip_no_dotnet: 24
- skip_ctc_max_30: 7
- already_applied: 4
- skip_ctc_max_31: 1
- skip_ctc_max_32.5: 1

## Code fix
- Branch: `cursor/naukri-fix-company-site-cta-c8ce` (pushed)
- Prefer **Go to company site** when **Apply on company site** is disabled (“Apply attempted”); hook `window.open`
- PR: create blocked (`gh` 403 Resource not accessible by integration) — branch ready for owner/PR merge

## Artifacts
- `/opt/cursor/artifacts/naukri-daily-run.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-company-site-pass.json`
