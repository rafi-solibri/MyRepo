# Foundit daily — 2026-08-15 (POST_FIX_RERUN=1 on merged #169)

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT JWT OK; `/home/ubuntu/.config/chrome-foundit`)
- Resume: `resumes/Rafi_Resume.docx` (preflight + `node tools/foundit/resume.js`; never stubbed)
- HEAD at apply start: `02e58e4` — `fix(hitechcity): complete Workday/guest career applies instead of walling JD chrome` (#169)
- This session Applied tab: **494 → 494** (+0)
- Intentional applies this session: **0** (do not invent)
- Already applied (userJobInfo / applicationStatus): **73** — skipped
- Classified skips: **1184**
- Blocked: **0**
- Age windows: 1 → 3 → 7 → 14 → 30 → 90 → 3650 days (inventory exhausted)
- Candidates: d1=76, d3=202, d7=209, d14=286, d30=258, d90=178, d3650=48
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run calls
- Runner: `node tools/foundit/daily_apply.js` exit 0

## Applied this session
None. Every remaining Hyd/remote Arch/Lead/EM/.NET candidate was already on the Applied tab or failed `classifyJob`.

## Earlier same-day Foundit applies (not this agent)
A prior post-fix re-run (`bc-a63ba793`, report on `cursor/foundit-daily-post-fix-re-run-2026-08-15-b13b`) already moved the Applied tab **457 → 489** (+32) on merged #164 + a filter pass. The tab is now **494** (further same-day runs / Falcon registrations between that report and this one). Those roles are **not** counted as applies by this agent.

## Top skip reasons (this session)
- no .NET on title+skills: 352
- location Bengaluru: 186
- no seniority keyword on title: 107
- location Pune: 60
- location Singapore (country-only / non-Hyd after `hasSpecificPlace`): 46
- SAP without .NET: 35
- junior/mid maxExp bands (max&lt;10): 56
- non-software engineering without .NET on title: 17
- pure AI/data without .NET on title: 12
- ServiceNow: 10
- infra/ops without .NET on title: 9
- Salesforce / Agentforce: 4
- Oracle Fusion/ERP without .NET on title: 4
- already applied today: 73

## Blocked
None (no login wall, no CAPTCHA stop, no Falcon/ATS failure this session).

## LinkedIn referral drafts
None this session (0 new applies). Not inventing drafts from earlier runs.

## Auto-fix
No new code-fixable Foundit blocker. #169 is a Hitech City Python ATS/Workday guest-apply fix; Foundit JS already uses `completeWorkdayApply` + `completeExternalPage`. Did **not** launch another post-fix re-run (inventory exhausted; same-day Foundit re-runs today including this one: 8, cap 20).
