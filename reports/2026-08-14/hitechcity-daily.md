# Hitech City / Knowledge City daily — 2026-08-14 (post-fix re-run)

POST_FIX_RERUN=1 on `main` @ `8e4652a` (#151 max-apply + #143 harvest/Salesforce skip).
Agent: https://cursor.com/agents/bc-8016b6dc-3dd4-4740-b299-e77aa6bbb667

## Counts (this session — do not invent)
- Applied (confirmed): **1**
- Referrals sent: **0**
- LinkedIn: 0 applied · 30 blocked · 157 skipped (then same-tab Workday hijack → 0 ids from Goldman onward)
- Careers: 0 applied · 32 blocked · 20 skipped · 27 portals scanned
- Boards: 1 applied · Naukri ok (+1) · Foundit 0 · Cutshort 0 · Instahyre 0 · Indeed error rc=5 (`indeed_login_required`)
- Discovery: +0 tenants (71 total; 37 metadata updates)
- Totals: **1** applied · 64 blocked · 3632 skipped · rc=0
- Resume: `resumes/Rafi_Resume.docx` | CTC **52 → 65 LPA** | notice 0

## Applied (confirmed)
1. **Software Product / Sangathr Career Management Consultants** — AI Full stack Application Architect (Naukri recommended, reported Remote; listing URL is Chennai). **Off-campus allowlist miss** — recommended/homepage path did not enforce the campus company allowlist. Fixed in this PR; already submitted so not re-applied.

## Already applied earlier today (skipped / not re-counted)
- ModMed — Indeed Easy Apply (original cron, credited after #143 harvest)
- Salesforce — Success Architect (service cloud) Indeed Easy Apply (false apply; filter in #143)
- S&P Global Market Intelligence — Associate Director (Naukri, earlier same-day re-run)
- Naukri +1 from original cron (unnamed in surviving artifacts)

## Campuses
Sattva Knowledge City / Knowledge Park, Mindspace Madhapur, The V, Cyber Pearl, DLF Cyber City, Divyasree Orion — campus tenant list (71 companies).

## Blockers
- **Code-fixed (this PR):** LinkedIn same-tab Workday ATS (GE Vernova `/job/Oslo/`) swallowed later company searches. Recover LinkedIn tab; skip non-Hyd ATS URLs; careers starts on a fresh tab.
- **Code-fixed (this PR):** Naukri recommended/homepage inventory ignored campus allowlist.
- **Owner:** Indeed board `indeed_login_required` (CF cleared, anonymous session) — headed login / home CDP.
- **Owner:** LinkedIn CAPTCHA/checkpoint on CDP relaunch after boards (first LinkedIn phase was signed in). Do not invent Easy Applies.
- Careers walls: CAPTCHA/bot (13), login/account (12, incl. Amazon passport), ATS incomplete (6). Experian Hyd .NET/Architect cards hit SmartRecruiters CAPTCHA.

## Artifacts
Cloud artifacts under `/opt/cursor/artifacts/` for this campus daily (summary + linkedin/careers/boards/discovery).
