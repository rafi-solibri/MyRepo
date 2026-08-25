# Foundit daily — 2026-08-25

- Login: MSSOAT + jwtOk=True; hiRafi false (Hi, Seeker placeholder) but cookie + onApp OK.
- Applied tab: **429 → 441** (+12). Intentional logged: **12**. Age → **3650d**.
- Candidates: d1=133 / d3=70 / d7=337 / d14=245 / d30=280 / d90=181 / d3650=38.
- Skips: 1200 | duplicates: 72 | blocked: 0.
- No `canJobApply` dry-run.
- Resume: `resumes/Rafi_Resume.docx` with per-apply JD tailor + profile upload.
- Preflight: older branch hit `DESTS[$i]` unbound (hirist already aligned on current `main`); Foundit cookies still synced before crash.

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

## Top 3 LinkedIn referral drafts
- **Infosys Limited / .Net production support Lead:** Hi — I'm applying for .Net production support Lead at Infosys Limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **Infosys Limited / .Net angular Lead:** Hi — I'm applying for .Net angular Lead at Infosys Limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **avalara apac / Senior Software Engineering Manager:** Hi — I'm applying for Senior Software Engineering Manager at avalara apac. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-25/foundit-apply-report.json`)

## Post-fix re-run (POST_FIX_RERUN=1, after #260 + #261)

Ran on `main` @ `5823080` (merged #261 resume compress + #260 filter skips). Preflight + Chrome CDP (`chrome-foundit`) + `node tools/foundit/daily_apply.js` exit 0.

- Login: MSSOAT + jwtOk=True; hiRafi false (Hi, Seeker) but cookie + onApp OK.
- Resume: `resumes/Rafi_Resume.docx` (20945 bytes after bootstrap compress).
- Applied tab: **441 → 441** (+0). Intentional logged: **0**. Age → **3650d**.
- Candidates: d1=135 / d3=70 / d7=335 / d14=247 / d30=278 / d90=179 / d3650=33.
- Skips: 1199 | duplicates: 78 | blocked: 0.
- No invented applies. No `canJobApply` dry-run. Eligibility via userJobInfo / applicationStatus.
- Today's morning applies skipped as duplicates (userJobInfo), including Infosys .Net Lead / avalara SEM / Jobgether Integration SA / Blue Yonder / realty EM / aarushi OSS.
- New filters confirmed (no re-apply):
  - ResultsCX **Sr. Director, Solutions Architect - AI** → `pure AI/data without .NET on title`
  - Infosys **UI Technical Architect React and Angular** → `UI/frontend React/Angular without .NET on title`
  - Jobgether **Senior Technical Lead - Asterisk & Telephony** → `Asterisk/telephony without .NET on title`
- Remaining inventory was already applied or filter-skipped. No new code-fixable blocker; no extra re-run launched (this is re-run 2/5 for Foundit on 2026-08-25).

Post-fix artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-25/foundit-apply-report-postfix.json`)
