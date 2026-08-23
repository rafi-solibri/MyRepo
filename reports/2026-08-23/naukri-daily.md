# Naukri daily — 2026-08-23 (post-fix re-run)

Same-day re-run on **merged #241** (`696dc31`). Morning cron did not apply with the fix (0 applies, 1 Globallogic `apply_unconfirmed`). This job pulled `main` first and ran `node tools/naukri/daily_apply.js` with that code. `POST_FIX_RERUN=1`. Re-run count: **1 / 5**.

## Profile resume refresh (STEP 0)
- **ok** — `profileUpdated: true`
- File: `resumes/Rafi_Resume.docx` (canonical; restored at end of run)
- UI: `Rafi_Resume.docx` / **Uploaded today** (`matchedToken: today`)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts
| Metric | Count |
| --- | --- |
| profileUpdated | **true** |
| Applied (confirmed) | **0** (none invented) |
| External / company-site completed | **0** |
| Blocked | **0** |
| Skipped (incl. duplicates) | 2593 |
| Unique skips | 227 |
| Seen | 208 |
| Tailored applies | 0 |

## Already applied today (not re-counted)
- Clean Harbors — .Net Fullstack Tech Lead (detail CTA Applied)
- First American — Staff Software Engineer (homepage; detail CTA Applied)

## Eligible inventory
Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Director with .NET (or generic Arch/Lead that #241 would still allow) was **thin**. Unique skip reasons:

| Reason | Unique |
| --- | --- |
| skip_title_keyword | 144 (Java / AI / Salesforce / Data / ServiceNow / SAP / D365 / cyber / QA) |
| skip_no_dotnet | 34 (PM / IC / AI-lead without Arch-Lead title) |
| skip_seniority | 28 (IC including some .NET engineers — not Lead/Arch) |
| skip_location | 7 |
| skip_company | 4 (Salesforce employer) |
| skip_ctc_max_30 / 32.5 | 5 (Incedo .Net Lead listed max 30 LPA — under 35) |
| hirist_login_required_skip | 3 |
| already_applied_detail | 2 |

## Hirist (skipped, not hard-blocked)
- Epam Systems — Full Stack Solution Architect — Node.js/AngularJS
- Anlage Infotech — Full Stack AI Manager
- Mancer Consulting Services — Engineering Manager - Platform

## #241 behavior this run
- Globallogic Principal AI/ML Engineer skipped via title (`skip_title_keyword`) — no false apply / no `apply_unconfirmed`
- No new code-fixable blocker. Did **not** launch another post-fix re-run.

## Artifacts
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- Compact copy: `reports/2026-08-23/naukri-daily-apply-summary.json`

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
This run: https://cursor.com/agents/bc-97475405-b444-446a-8f79-ad1dfc940574
Merged fix: https://github.com/rafi-solibri/MyRepo/pull/241
