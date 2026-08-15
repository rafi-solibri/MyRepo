# Foundit daily — 2026-08-15

Post-fix re-run on merged `main` (`423bd87` / [PR #159](https://github.com/rafi-solibri/MyRepo/pull/159)).
Automation: https://cursor.com/automations/5d1b07b2-90a9-11f1-ba66-0e7d0216e441
This job: https://cursor.com/agents/bc-1ac74564-6b04-4142-9010-1a2ffdcf9990
Morning cron: https://cursor.com/agents/bc-09b4932e-09a3-4ff0-a736-596de3a9123b

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (`hasRafi`, MSSOAT JWT OK; `/seeker/dashboard`)
- Resume: `/workspace/resumes/Rafi_Resume.docx` (52 → 65 LPA)
- Morning cron Applied tab: **401 → 405** (+4)
- Post-fix re-run Applied tab: **405 → 405** (+0) — already-applied skipped; no invented applies
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run calls
- No new code-fixable blocker (re-run cap unused)

## Applied (morning cron only — not re-applied)
All four were Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `linkedin_no_easy_apply` (Foundit count moved; LinkedIn Easy Apply did not complete):

1. **relq technologies** — Senior .NET Full Stack Developer- India — jobId `62693974` — https://www.linkedin.com/jobs/view/4451557133/
2. **Closeloop Technologies** — Web Engineering Manager — jobId `62680103` — https://www.linkedin.com/jobs/view/4451669960/
3. **Kumaran Systems** — Lead .Net Developer — jobId `62683340` — https://www.linkedin.com/jobs/view/4452392398/
4. **infomatix web technologies llp** — Senior .NET Full Stack Engineer — jobId `62692059` — https://www.linkedin.com/jobs/view/4451956671/

## Post-fix re-run (this job)
- Queries: `.net architect`, `.net lead`, `solutions architect .net`, `engineering manager .net`, `principal .net`, `azure .net architect`, `software architect .net`
- Age window: **3650d** (1→3→7→14→30→90→3650)
- Candidates: d1=45, d3=42, d7=66, d14=127, d30=136, d90=110, d3650=13
- Intentional applies this run: **0**
- Duplicates (`userJobInfo`): **43** (includes today's 4 plus prior-day Foundit applies)
- Skipped: **496**
- Blocked: **0**

## Top skip reasons (re-run)
- no .NET on title+skills: 137
- no seniority keyword on title: 106
- location not Hyd/remote (Bengaluru 74, Pune 26, Noida 13, …)
- junior/mid `maxExp` bands / WPF / SAP / CTC under 35 LPA

## LinkedIn referral drafts (from morning applies)
1. relq technologies — Senior .NET Full Stack Developer- India — 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA.
2. Closeloop Technologies — Web Engineering Manager — same profile; ask HM referral.
3. Kumaran Systems — Lead .Net Developer — same profile; Rafi_Resume.docx.

## Notes
- Recurring ATS gap: Foundit SCRAPPING redirects → LinkedIn with no Easy Apply. Treated as known limitation, not a new helper fix.
- Merged #159 is Hitech City (Architecture titles / junk LinkedIn tenants). Foundit helpers on this `main` already include prior-day Salesforce/Agentforce skip (#140).
