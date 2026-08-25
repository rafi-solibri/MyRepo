# Foundit daily — 2026-08-25 (POST_FIX_RERUN=1)

Same-day re-run on merged `main` (`c507fd2`, includes #257 sync-chrome-sessions hirist arrays). Earlier Foundit cron did **not** apply with that fix; this job did.

- Login: MSSOAT + `jwtOk=true`; `hiRafi` false (Hi, Seeker placeholder) but cookie + onApp OK.
- Resume: `resumes/Rafi_Resume.docx` (3,957,700 bytes). No `canJobApply` dry-run.
- Applied tab: **441 → 441** (+0). Intentional logged: **0**. Age → **3650d**.
- Skips: 1201 | duplicates: 83 (`userJobInfo`) | blocked: 0.
- Eligible Hyd/remote Arch/Lead/.NET inventory was already applied (prior days + skip-already-applied). **No invented applies.**

## Applied

None this run.

## Already applied (skipped — do not re-submit)

83 roles already on the account via `userJobInfo`, including:

- Infosys — .Net angular Lead / .Net production support Lead
- avalara apac — Senior Software Engineering Manager
- quik hire staffing — Solutions Architect (Remote)
- Blue Yonder — Sr Enterprise Technical Architect (SCPO)
- Globallogic Ukraine — Product Security Architect IRC286354
- Taskus — Endpoint Solution Architect
- Accenture — Solution Architect
- Photon — Technical Architect_GNC_Offshore
- Microsoft — Solution Architect Manager / Principal Consultant - Dotnet Full stack & AI
- Hyland — Senior Software Architect - .NET
- Cimpress — Lead Software Engineer(.Net)-Remote
- Persistent — .NET Lead
- blackbaud india — Laureate - .Net Architect

## Top skip reasons

| Count | Reason |
| --- | --- |
| 363 | no .NET on title+skills |
| 200 | location Bengaluru / Bangalore |
| 113 | no seniority keyword on title |
| 67 | SAP without .NET |
| 43 | location Pune |
| 34 | location Singapore |
| 23 | pure AI/data without .NET on title |
| 16 | non-software engineering without .NET on title |
| 15 | infra/ops without .NET on title |
| 1 | Guidewire (post-#240 filter still holds) |

Filters look correct: Bangalore/Pune .NET Arch/Lead skipped on location; Mainframe/Java/Salesforce/Python-primary titles skipped; Guidewire still skipped. No new code-fixable blocker.

## Blocked / ATS notes

None. Falcon/ATS not invoked (0 new eligible after already-applied skip).

## Top 3 LinkedIn referral drafts

None — 0 new applies this run (do not invent).

## Auto-fix / re-run cap

- Merged PR that triggered this re-run: https://github.com/rafi-solibri/MyRepo/pull/257
- This is Foundit post-fix re-run **1 of 5** for 2026-08-25 IST.
- No new helper patch. Do not launch another Foundit re-run for this report-only commit.

Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-25/foundit-apply-report.json`)
