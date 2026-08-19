# Naukri daily — 2026-08-19 (post-fix re-run)

Automation: [Naukri Daily 9 AM](https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441)
Agent: https://cursor.com/agents/bc-2ca71497-dafe-4f15-8ec4-b14c1dd34532
Code: `origin/main` @ `7f1a3b9` plus in-session fixes on `cursor/naukri-daily-post-fix-re-run-2026-08-19-88ca`
Resume: `resumes/Rafi_Resume.docx`

## 1) Profile resume refresh
- **ok** — `profileUpdated: true`, `todayHit: true`, matched token `today`
- Filename shown: **Rafi_Resume.docx** (Uploaded today)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## 2) Confirmed Naukri Quick Apply (chatbot thanks / Applied)
| Company | Role | Location | Path | Resume | Job |
| --- | --- | --- | --- | --- | --- |
| Solugenix | Lead Full stack Engineer - Azure | Hybrid Hyd / Indore / Bengaluru | Naukri | Rafi_Resume.docx | [listing](https://www.naukri.com/job-listings-lead-full-stack-engineer-azure-solugenix-indore-hyderabad-bengaluru-10-to-20-years-290626001271) |
| Agilisium | Solution Architect | Hyd / Chennai / Bengaluru | Naukri | Rafi_Resume.docx | [listing](https://www.naukri.com/job-listings-solution-architect-agilisium-hyderabad-chennai-bengaluru-12-to-18-years-180826047334) |
| Intrics Solutions | Senior / Lead .Net FullStack Developer | Hyderabad | Naukri | Rafi_Resume.docx | [listing](https://www.naukri.com/job-listings-senior-lead-net-fullstack-developer-intrics-solutions-hyderabad-10-to-20-years-180826040348) |

## Wrong-title submits (now skipped)
These chatbot-confirmed on pass 1 before the filter patch. Pass 2 skipped them.

| Company | Role | Why wrong |
| --- | --- | --- |
| Progressive Infovision (PIPL) | EDI Integration Architect | EDI-primary |
| Vertex Computer Systems | MuleSoft Architect/Lead | MuleSoft-primary |

## Not counted (do not invent)
| Company | Role | Why |
| --- | --- | --- |
| Tekskills | Auth0 Architect | `view_applied_jobs` chip only |
| Tekskills | Lead Dot Net Developer | `view_applied_jobs` chip only |
| Qentelli | Database Architect | `view_applied_jobs` chip only |
| Solugenix | Lead Full stack Engineer - Azure (listing `180826013658`) | Pass 2 `disabled:Quick apply Applied` — already applied today |

## External / company site
- **0 completed**
- Broadcom Staff Software Engineer (Hyd) — Workday My Information stuck on ALL-CAPS names + invalid +91 phone (`external_incomplete_or_timeout`). **Fixed** in `workday_apply.js` (not used for this listing after timeout).
- UST Software Architect II — RippleHire `.../candidate/unknownerror`. **Fixed** fail-fast.

## Blocked
- Tekskills Cloud Solutions Architect — `apply_unconfirmed` / `no_chat`
- Tekskills Solution Architect — `apply_unconfirmed` / `no_chat`
- Tekskills Principal Engineer — `apply_unconfirmed` / `no_chat`
- Principal Financial Group Associate Director - Engineering — `chat_steps_exhausted` (recurring)
- Hirist: 6× `hirist_login_required_skip` (soft)

## Recruiter chat
None sent (`recruiterNote: false` on all confirms).

## Counts
| | Pass 1 (merged main) | Pass 2 (branch fixes) |
| --- | --- | --- |
| profileUpdated | true | true |
| applied (script rows) | 8 | 1 (already-applied Solugenix listing) |
| applied (honest chatbot) | 5 (incl. 2 wrong-title) | 0 new |
| external | 0 | 0 |
| blocked | 5 | 2 |
| skipped | 818 | 2810 |
| seen | 126 | 229 |

Honest unique confirmed applies today: **3** (Solugenix Azure Lead, Agilisium SA, Intrics .NET Lead). Plus 2 wrong-title chatbot submits already on Naukri.

## Code fixes this run (branch, PR pending GitHub permission)
- `tools/naukri/workday_apply.js` — title-case names, 10-digit IN mobile, overwrite autofill
- `tools/naukri/daily_apply.js` — View applied jobs never confirms; RippleHire unknownerror fail-fast
- `tools/naukri/resume_and_filters.js` — skip MuleSoft / EDI / Auth0 / database architect

Logged in `automation-prompts/issues/naukri.md`. Tests: `node tools/naukri/test_workday_apply.js`, `node tools/naukri/test_filters.js`.
