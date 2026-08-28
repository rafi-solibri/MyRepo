# Naukri daily — 2026-08-28 (post-fix re-run, this session)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
Run: https://cursor.com/agents/bc-01b0c57b-1323-4740-bcc3-aabf1b9874ce
Code at start: `main` @ `5a71a82` (includes #282 / #280). `POST_FIX_RERUN=1`.

## 1) Profile resume refresh
- **ok** — `profileUpdated: true`
- Filename shown: **Rafi_Resume.docx**
- Signal: **Uploaded today**
- Restored canonical CV at end of run: **ok**

## 2) Counts
| metric | n |
| --- | --- |
| applied | 1 |
| external ATS completed | 0 |
| blocked | 0 |
| skipped | 3077 |
| seen | 215 |
| tailored applies | 1 |

## Applied this session (do not invent)
- Manpowergroup / IT Services — **Senior VDI Architect (Citrix & Azure Virtual Desktop)** — Hyderabad — Naukri chatbot (`chatbot:responses_thanks`) — tailored `Rafi_Resume.docx`
  - https://www.naukri.com/job-listings-senior-vdi-architect-citrix-azure-virtual-desktop-manpowergroup-services-india-hyderabad-10-to-19-years-280826003933
  - **False apply** (Citrix/AVD desktop virtualization, not .NET SA). Filter fix pushed on `cursor/naukri-daily-post-fix-re-run-2026-08-28-ab61`.

## Already applied earlier today (not re-counted)
- Clean Harbors — .Net Fullstack Tech Lead (`already_applied_detail`)

## Blocked
- none

## External / company-site
- none completed this session

## Code fix this run (pushed, PR create blocked by integration permissions)
- `tools/naukri/resume_and_filters.js`: skip `vdi` / `citrix` / `azure virtual desktop` / `avd` / `virtual desktop`
- Tests: `node tools/naukri/test_filters.js` OK
- Issue log: `automation-prompts/issues/naukri.md`

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-daily-apply.log`
