# Issues from last cron + fixes

## Fixed in this repo

| Issue | Fix |
| --- | --- |
| `Rafi_Resume_Architect.docx` missing → agents invented stubs or used portal-only resume | Canonical **`resumes/Rafi_Resume.docx`** (your upload) + `scripts/bootstrap-job-assets.sh` copies to Documents/resumes/Downloads; legacy Architect filename is a same-file alias |
| LinkedIn Easy Apply looked for Architect label | Scripts use label **Rafi_Resume**; external ATS uploads canonical docx |
| Cutshort questionnaires locked empty (9/11) | Documented correct API payload in `tools/cutshort/questionnaire.js` — never `screeningSubmitted` before verified answers |
| Naukri Coupa/Pega / Intern≈Internet false applies | Filters in `tools/naukri/resume_and_filters.js` |
| Foundit `canJobApply` accidental submit | Explicit forbid in `tools/foundit/resume.js` + prompts |
| LinkedIn Bengaluru false-allow via page body "Hyderabad" | Prompts: location from top card / workplace pills only |
| Agents rediscovering tools each run | Durable helpers under `tools/linkedin`, `tools/cutshort`, `tools/naukri`, etc. |
| Naukri profile resume not refreshed daily | `tools/naukri/update_profile_resume.js` + STEP 0 in Naukri prompt re-uploads `Rafi_Resume.docx` every run for recruiter freshness |

## Fixed for 2026-08-06 “automations did not run”

| Issue | Fix |
| --- | --- |
| Cron fired but 0 applies (login walls) | Agents used empty CDP profiles while you logged into Default Chrome |
| Session mismatch | `scripts/sync-chrome-sessions.sh` + `tools/chrome_session.js` copy Default → all portal CDP profiles |
| Naukri false-skips on SA roles | Title skip no longer matches bare `QA`; detail scans must not use full `document.body` |
| General Daily noise | Documented: **disable** General Daily (research-only, 0 applies) |

## Still requires your action (cannot fix from code alone)

| Blocker | Who | What to do |
| --- | --- | --- |
| Snapshot without Default Chrome logins | You | Confirm Desktop Chrome logins → `bash scripts/sync-chrome-sessions.sh` → **Save/Update snapshot** |
| Indeed Cloudflare 403 on datacenter IP | You | Attach a **private worker** (residential IP) |
| Resend notification email not sent | You | Authenticate **Resend MCP** + set secret `RESEND_FROM_EMAIL` |
| Greenhouse / ATS email OTP | Optional | Keep Gmail logged in same Chrome profile |
| Portal passwords | Optional | Add secrets if interactive login is not snapshotted |
| General Daily duplicate | You | Disable https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441 |

## After merging this PR

1. Re-paste updated prompts from `automation-prompts/0*.md` into each automation (resume section changed).
2. Merge to `main` (or point automations at this branch) so cron checkouts include `resumes/Rafi_Resume.docx`.
3. Complete portal logins + snapshot once.
4. For Indeed: enable private worker.
5. For Notification: connect Resend MCP + `RESEND_FROM_EMAIL`.
