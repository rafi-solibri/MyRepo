# Naukri Daily — 2026-08-15 (post-fix re-run)

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` | Expected 65 LPA / Current 52 LPA | Hyd + Remote

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
Run: https://cursor.com/agents/bc-eb11dfcc-a670-47a6-8f22-81c090f97edb
Code: `main` @ `3fc57c3` (#163 ATS password alias) then same-session fix `881fc02`

This is the **5th** same-day Naukri post-fix cloud re-run (cap 5). No further cloud re-run launched.

## STEP 0 — Profile resume refresh
- **profileUpdated:** `true`
- **verify:** Resume / Update / Rafi_Resume.docx / Uploaded today (`matchedToken: today`)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts (confirmed only — no invented applies)
- profileUpdated: **true**
- applied: **2**
- externalCompleted: **0**
- blocked: **10**
- skipped: **3388** (seen 201)
- expandedAges: `[15, 30, 60]` (early expand after age-1 applied=0)

## Applied
| Company | Role | Location | Path | Resume |
| --- | --- | --- | --- | --- |
| Salesforce | Success Architect - Industry Specific | Hybrid - Hyderabad, Bengaluru | Naukri Quick Apply (`chatbot:responses_thanks`) | Rafi_Resume.docx |
| Naukri Assist | Associate Manager, Infra Platform Engineer | Hyderabad | Naukri Quick Apply (`chatbot:responses_thanks`) | Rafi_Resume.docx |

Already applied earlier today (skipped): i2e Consulting Solution Architect; Clean Harbors .Net Fullstack Tech Lead.

## Blocked (not counted as applied)
- Tanisha Systems | Technical Product Manager — Pharmacy Software Solutions | `apply_unconfirmed` / chat_steps_exhausted
- Salesforce | Manager, Software Engineering - Release Engineering | Workday `ats_login_wall`
- Reputed MNC (Flexi Careers) | Manager - AI & Cloud Solutions Engineering | `apply_unconfirmed`
- Highradius | Program Manager (Cloud Engineering) | `apply_unconfirmed` (View applied jobs)
- Coupa | Manager, Software Engineering (.Net with React) | Lever `external_incomplete_or_timeout` (hCaptcha)
- Salesforce | Readiness Architect-Industry | Workday `external_incomplete_or_timeout`
- Salesforce | Success Architect - SFMC | Workday `ats_login_wall`
- Trinet Group | Manager, Software Engineering | Oracle Cloud `external_incomplete_or_timeout`
- Salesforce | Software Engineering Architect | Workday `external_incomplete_or_timeout` (Bangalore WD URL; Naukri loc Hyderabad)
- Principal Financial Group | Associate Director - Engineering | `apply_unconfirmed` / chat_steps_exhausted

## Skip reasons (top)
- duplicate_in_run: 3178
- skip_title_keyword: 134
- skip_seniority: 29
- skip_no_dotnet: 28
- skip_ctc_max_30 / 31 / 32.5: 9 (listed max clearly under 35 LPA — Valuelabs .NET Architect, Incedo .Net Lead, Sonata Azure SA, …)
- skip_location: 7
- already_applied_detail: 2

## Code fix this run
First pass on #163 alone: **0 applies** — homepage cards parsed empty role (CTA last) and `decideSkip` treated company chrome (**Salesforce**) as a title keyword, false-skipping Architect / EM cards.

Fix on `cursor/naukri-daily-post-fix-re-run-2026-08-15-2364` (`881fc02`):
- `parseNaukriCardLines` for search + homepage layouts
- `shouldSkipTitleFromCard` uses job title only
- Same-session re-run then confirmed the 2 Naukri applies above

`gh pr create` failed (`Resource not accessible by integration`). Branch is pushed for owner merge. Already at the 5-rerun cap — **do not launch a 6th cloud job**.

## Owner-only
- Salesforce Workday login walls / timeouts
- Coupa Lever hCaptcha
- Trinet Oracle Cloud ATS incomplete

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-daily-apply-pass1.json` (0-apply first pass)
