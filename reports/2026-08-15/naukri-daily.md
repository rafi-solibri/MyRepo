# Naukri daily — 2026-08-15 (post-fix re-run after #161)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
This run: https://cursor.com/agents/bc-0b8582b4-a11e-4155-ae40-569884e7a672
Merged incoming: https://github.com/rafi-solibri/MyRepo/pull/161 (`92bb3cc`), then rebased onto #163 (`3fc57c3`).

## Profile resume refresh
- **ok** — `profileUpdated: true`
- Resume file: **Rafi_Resume.docx**
- UI: “Uploaded today” (`matchedToken: today`)
- Headline not touched (`headline_input_missing`)

## This re-run counts (final pass, title-skip + homepage parse)
- profileUpdated: **true**
- applied: **0** (none invented)
- externalCompleted: **0**
- blocked: **8**
- skipped: 811 · seen: 112

Already applied earlier today (skipped here, not counted as this run):
- i2e Consulting — Solution Architect (Remote)
- Clean Harbors — .Net Fullstack Tech Lead (Hyderabad)
- Jade Global / LRR Technologies / PwC Technical Lead / Xanika PROS CPQ SA (earlier Naukri agents)

## Applied this re-run
None confirmed.

## Blocked
| Company | Role | Path | Reason |
| --- | --- | --- | --- |
| Salesforce | Senior Manager, Software Engineering | company_ATS Workday | `external_incomplete_or_timeout` — https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site/job/India---Hyderabad/Senior-Manager--Software-Engineering_JR312176 |
| Salesforce | Manager, Software Engineering - Release Engineering | company_ATS | `external_link_not_opened` |
| Salesforce | Readiness Architect-Industry | company_ATS | `external_link_not_opened` |
| Salesforce | Success Architect - SFMC | company_ATS | `external_link_not_opened` |
| Salesforce | Success Architect - Industry Specific | Naukri | `quick_apply_not_found` |
| Sonata Software | Azure Solution Architect | Naukri | `apply_unconfirmed` / `no_chat` |
| i2e Consulting | Solution Architect | Naukri | `quick_apply_not_found` (already applied today) |
| Clean Harbors | .Net Fullstack Tech Lead | Naukri | `quick_apply_not_found` (already applied today) |

Resume used on every attempt: `resumes/Rafi_Resume.docx`.

## Code fixes pushed (PR create blocked — `gh` integration cannot open PRs)
Branch: `cursor/naukri-daily-post-fix-re-run-2026-08-15-24ca`

1. Homepage/recommended cards put CTA last → empty role → 0 homepage applies. `parseNaukriCardLines` keeps search CTA-then-role and parses CTA-last homepage layout.
2. `decideSkip` scanned the first 8 card lines (company + skills). Salesforce chrome false-skipped **Senior Manager, Software Engineering** (Hyd, company site). Title skips are role-only. CTO counts as director-band.

Owner: open/merge that branch into `main` (`bash scripts/auto-merge-fix-pr.sh` after `gh` write is allowed). Naukri post-fix re-run count today including this job: **3/5**.
