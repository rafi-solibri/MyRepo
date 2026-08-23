# Foundit daily — 2026-08-23

- Login: MSSOAT + jwtOk=True; hiRafi false (Hi, Seeker placeholder) but cookie + onApp OK.
- Applied tab: **440 → 445** (+5). Intentional logged: **5**. Age → **3650d**.
- Skips: 1187 | duplicates: 71 | blocked: 0.
- No `canJobApply` dry-run.
- Resume: `resumes/Rafi_Resume.docx` with per-apply JD tailor + profile upload.

## Applied
1. Globallogic Ukraine — Product Security Architect IRC286354 — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
   - path: Foundit + ATS https://www.linkedin.com/jobs/view/4456021081/
2. Accenture — Solution Architect — Falcon `NORMAL` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://www.monsterindia.com/event/triumph/
3. Photon Interactive Private limited — Technical Architect_GNC_Offshore — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://fa-ertb-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/26527/
4. ValueMomentum — Guidewire Technical Lead — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
   - path: Foundit + ATS https://www.linkedin.com/jobs/view/4454231946/
5. Taskus — Endpoint Solution Architect — Falcon `NORMAL` (native Foundit)
   - path: Foundit Falcon

## Blocked / ATS notes
- None blocked. LinkedIn SCRAPPING jobs often `linkedin_no_easy_apply`; Accenture triumph + Photon Oracle CX timed out under ATS cap.

## False applies / code fix
- ValueMomentum **Guidewire Technical Lead** passed via Arch/Lead exception (Duck Creek already skipped; Guidewire missing) → fixed+merged https://github.com/rafi-solibri/MyRepo/pull/240 (`tools/foundit/filters.js` Naukri/LinkedIn/Instahyre parity).

## Post-fix re-run (#240)
- Applied tab: **446 → 446** (+0). Intentional logged: **0** (inventory already Applied / filters skip).
- Guidewire Technical Lead now correctly skipped (`reason: Guidewire`).
- Skips: 1193 | duplicates: 76 | blocked: 0.

## Top 3 LinkedIn referral drafts
- **Globallogic Ukraine / Product Security Architect IRC286354:** Hi — I'm applying for Product Security Architect IRC286354 at Globallogic Ukraine. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **Accenture / Solution Architect:** Hi — I'm applying for Solution Architect at Accenture. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **Photon Interactive Private limited / Technical Architect_GNC_Offshore:** Hi — I'm applying for Technical Architect_GNC_Offshore at Photon Interactive Private limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)

## Post-fix re-run (#244 resume master)
- Ran on `main` after https://github.com/rafi-solibri/MyRepo/pull/244 (`Mohammed_Abdul_Rafi_Ahmed_Resume.docx` → `resumes/Rafi_Resume.docx`, 3.6MB). `POST_FIX_RERUN=1` / date 2026-08-23 IST.
- Login: MSSOAT + jwtOk=True; hiRafi false (Hi, Seeker) but cookie + onApp OK. Preflight + Chrome CDP foundit profile OK. No `canJobApply` dry-run.
- Applied tab: **451 → 452** (+1). Intentional logged: **1**. Age → **3650d**.
- Skips: 1180 | duplicates: 73 | blocked: 0.
- Morning applies skipped as already applied (`userJobInfo`): Globallogic IRC286354, Accenture Solution Architect, Photon Technical Architect_GNC_Offshore, Taskus Endpoint Solution Architect.
- ValueMomentum **Guidewire Technical Lead** still skipped (`reason: Guidewire`) — #240 holds.
- Resume: JD-tailored from new master; Foundit profile upload OK before Falcon.

### Applied this re-run
1. Hitachi Energy — Solution Architect — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://hitachi.wd1.myworkdayjobs.com/en-US/hitachi/job/Remote---Karnataka-India/Solution-Architect_R0130310
   - tailored headline: Solution Architect — AWS, Azure, Kubernetes; profileUploadOk=true
   - Workday reached Autofill with Resume then hit the 6.5m ATS cap (same Hitachi Workday pattern as morning — owner login, not a new code-fixable filter bug). No extra post-fix re-run launched.

### Referral draft (this re-run)
- **Hitachi Energy / Solution Architect:** Hi — I'm applying for Solution Architect at Hitachi Energy. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)

Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-23/foundit-apply-report.json`)
