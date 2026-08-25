# Foundit daily — 2026-08-25

- Login: MSSOAT + jwtOk=True; hiRafi false (Hi, Seeker placeholder) but cookie + onApp OK.
- Applied tab: **429 → 441** (+12). Intentional logged: **12**. Age → **3650d**.
- Candidates: d1=133 / d3=70 / d7=337 / d14=245 / d30=280 / d90=181 / d3650=38.
- Skips: 1200 | duplicates: 72 | blocked: 0.
- No `canJobApply` dry-run.
- Resume: `resumes/Rafi_Resume.docx` with per-apply JD tailor + profile upload.
- Preflight: `sync-chrome-sessions.sh` exited unbound on `DESTS[$i]` (hirist missing from DESTS/COOKIE_SETS/REQUIRED) — Foundit cookies still synced before crash.

## Applied
1. Infosys Limited — .Net production support Lead — Falcon `APPLY_REDIRECT_STAGE_NONE` / ATS `external_incomplete_or_timeout` (Infosys SSO)
2. Infosys Limited — .Net angular Lead — Falcon `APPLY_REDIRECT_STAGE_NONE` / ATS `external_incomplete_or_timeout`
3. avalara apac — Senior Software Engineering Manager — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
4. ResultsCX — Sr. Director, Solutions Architect - AI — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply` (**false apply**)
5. Jobgether — Sr. Solutions Architect/Senior Enterprise Integration Architect - Finance Systems — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
6. quik hire staffing — Solutions Architect (Remote) — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
7. Infosys Limited — Senior Global Deal Solution Architect (GCCCOE - JL7) — Falcon `APPLY_REDIRECT_STAGE_NONE` / ATS `external_incomplete_or_timeout`
8. Blue Yonder — Sr Enterprise Technical Architect (SCPO) — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
9. Infosys Limited — UI Technical Architect React and Angular — Falcon `APPLY_REDIRECT_STAGE_NONE` / ATS `external_incomplete_or_timeout` (**false apply**)
10. realty of america — Engineering Manager — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
11. Jobgether — Senior Technical Lead - Asterisk & Telephony — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply` (**false apply**)
12. aarushi infotech — Senior OSS Applications Architect Strategy — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`

## Blocked / ATS notes
- None blocked. LinkedIn SCRAPPING jobs often `linkedin_no_easy_apply`; Infosys career SSO timed out under ATS cap.

## False applies / code fix
- ResultsCX **Solutions Architect - AI**, Infosys **UI Technical Architect React and Angular**, Jobgether **Asterisk & Telephony** passed via Arch/Lead exception → `tools/foundit/filters.js` Instahyre-parity title skips + tests.
- `scripts/sync-chrome-sessions.sh`: add hirist DEST/`token` COOKIE/REQUIRED so PORTALS arrays align (fixes preflight unbound variable).

## Top 3 LinkedIn referral drafts
- **Infosys Limited / .Net production support Lead:** Hi — I'm applying for .Net production support Lead at Infosys Limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **Infosys Limited / .Net angular Lead:** Hi — I'm applying for .Net angular Lead at Infosys Limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **avalara apac / Senior Software Engineering Manager:** Hi — I'm applying for Senior Software Engineering Manager at avalara apac. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-25/foundit-apply-report.json`)
