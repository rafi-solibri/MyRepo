# Foundit daily — 2026-08-20

- Login: OK (`jwtOk=true`, `loggedIn=true`, Hi Rafi)
- Resume: `/workspace/resumes/Rafi_Resume.docx`
- Applied tab: **505 → 507** (delta +2 intentional)
- Age window used: `3650`
- Duplicates: 71 | Skips: 1202 | Blocked: 0
- No `canJobApply` dry-run

## Applied (first pass)

1. Socnet Technologies Private Limited — Senior Technical Lead - Agentic AI / Generative AI — Foundit Falcon (`NORMAL`) — **false apply** → fixed+merged https://github.com/rafi-solibri/MyRepo/pull/215
2. Zensar Technologies — Talkdesk Technical Lead/SME — Foundit + ATS https://www.linkedin.com/jobs/view/4452818405/ (`linkedin_no_easy_apply`)

## Post-fix re-run (same day) — AI title filter

- Applied tab: **507 → 507** (+0)
- Socnet `63331139` now skipped: `pure AI/data without .NET on title`
- Capgemini / Adobe Agentic AI titles also skipped by expanded filter
- Intentional applies: 0

## Post-fix re-run (same day) — JD-tailored resume on merged main (`POST_FIX_RERUN=1`)

- Head: `242000e` includes Foundit tailor https://github.com/rafi-solibri/MyRepo/pull/221 and Indeed tailor https://github.com/rafi-solibri/MyRepo/pull/223
- Preflight: `Rafi_Resume.docx` + Foundit `MSSOAT` cookies OK; Chrome CDP `/home/ubuntu/.config/chrome-foundit`
- Login: OK (`jwtOk=true`, `loggedIn=true`, live `wait_for_cdp_login` Hi Rafi)
- Applied tab: **507 → 507** (delta +0) — no invented applies
- Age window used: `3650`
- Duplicates: 72 (already applied; includes Zensar Talkdesk `63362118`) | Skips: 1205 | Blocked: 0
- Intentional applies this re-run: **0** (eligible Hyd/remote .NET Arch/Lead inventory already submitted today)
- JD-tailor + profile upload ran for 0 jobs because Falcon apply is gated behind `userJobInfo` / `applicationStatus` skip-already-applied
- No `canJobApply` dry-run
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`

## Top skip reasons (first pass)

- 334: no .NET on title+skills
- 184: location not Hyd/remote: Bengaluru / Bangalore | India
- 112: no seniority keyword on title
- 50: location not Hyd/remote: Pune | India
- 49: location not Hyd/remote: Singapore
- 38: SAP without .NET
- 28: location not Hyd/remote: Noida | India
- 27: location not Hyd/remote: Chennai | India
- 25: maxExp 7<10 (junior/mid band)
- 19: non-software engineering without .NET on title

## LinkedIn referral drafts (top 3)

1. **Socnet / Senior Technical Lead - Agentic AI / Generative AI** (false apply — do not use): Hi — I'm applying for Senior Technical Lead - Agentic AI / Generative AI at Socnet Technologies Private Limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
2. **Zensar / Talkdesk Technical Lead/SME**: Hi — I'm applying for Talkdesk Technical Lead/SME at Zensar Technologies. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

## Artifact

- `/opt/cursor/artifacts/foundit-apply-report.json`
