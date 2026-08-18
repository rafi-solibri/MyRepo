# Naukri daily — 2026-08-18 (post-fix re-run)

HEAD: `46012f5` plus same-day filter/ATS confirmation fix on this branch.
Resume: `resumes/Rafi_Resume.docx`

## STEP 0 — profile resume refresh
- **ok** — `profileUpdated: true`, `todayHit: true`, filename `Rafi_Resume.docx` (`Uploaded today`)
- Uploaded via `input[id*='resume' i][type='file']` + Update

## Counts
- profileUpdated: **true**
- applied (chatbot-confirmed): **8**
- applied (unconfirmed `view_applied_jobs` — do not treat as success going forward): **3**
- external / company-site completed: **0**
- blocked: **8**
- skipped: **762**
- seen: **103**

## Chatbot-confirmed Naukri applies
| Company | Role | Location | Resume |
| --- | --- | --- | --- |
| Tech Mahindra | Technical Architect | Hybrid - Hyderabad, Chennai, Bengaluru | Rafi_Resume.docx |
| 300plus Innovative Solutions | Solution Architect | Hyderabad | Rafi_Resume.docx |
| Cognizant | Copilot Studio Architect | Hybrid - Hyderabad, Chennai, Bengaluru | Rafi_Resume.docx |
| Sonata Software | Copilot Architect | Hybrid - Hyderabad, Chennai, Bengaluru | Rafi_Resume.docx |
| Highradius | Senior Manager -Techops | Hyderabad | Rafi_Resume.docx |
| Cubic Transportation | Software Engineering Manager | Hyderabad | Rafi_Resume.docx |
| Grid Dynamics | Architect | Hyderabad, Chennai, Bengaluru | Rafi_Resume.docx |
| WinWire | Technical Lead / Sr Technical Lead - Power BI, SQL | Hyderabad, Bengaluru | Rafi_Resume.docx |

## Unconfirmed (View applied jobs chip — not counted after this fix)
- Infosys — UI Technical Architect React and Angular
- Infosys — Lead Technical Architect Modern C Plus and Enterprise Systems
- Experian — Senior Staff Engineer ( AI )

## Blocked
- Optum / UnitedHealth — Architect (`external_incomplete_or_timeout`)
- UST — Architect I ManageEngine + Software Architect II (`ripplehire unknownerror`)
- Accenture — Enterprise SA + Associate Manager (`b2clogin` SSO burned as timeout)
- Backbase — Solution Architect (`external_incomplete_or_timeout`)
- Cognizant — SPFx Architect (`apply_unconfirmed` / no_chat)
- Experian — Lead Software Engineer(.Net + AWS) (`apply_unconfirmed` / no_chat)

## Code fix this run
- `confirmApplied` no longer treats page-level "View applied jobs" as success
- Title skips: Copilot Studio/Architect, Power BI, C++/C Plus, Engineer (AI), Techops, SPFx
- Accenture B2C / `candidate.accenture.com` fail-fast as `ats_login_wall`; close leaked SSO tabs
- RippleHire `/candidate/unknownerror` fail-fast as unavailable
