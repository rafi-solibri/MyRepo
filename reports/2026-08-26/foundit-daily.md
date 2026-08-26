# Foundit daily — 2026-08-26

- Login: MSSOAT + jwtOk=True; hiRafi confirmed (`wait_for_cdp_login.js`).
- Applied tab: **445 → 450** (+5). Intentional logged: **5**. Age → **3650d**.
- Candidates: d1=49 / d3=167 / d7=258 / d14=300 / d30=270 / d90=192 / d3650=38.
- Skips: 1197 | duplicates: 72 | blocked: 0.
- No `canJobApply` dry-run.
- Resume: `resumes/Rafi_Resume.docx` with per-apply JD tailor + profile upload.

## Applied
1. Globallogic India — Senior .NET Lead (Principal Engineer) IRC296129 — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
2. Capgemini — PU1 Support- Architect - Offshore Manager — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout` (SuccessFactors/SAPBTP) (**false apply**)
3. blackbaud india — Software Engineer, Principal - .NET Developer — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
4. Blue Yonder — Sr Enterprise Technical Architect (Planning) - GPTS Consulting — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
5. Cyient — Manufacturing Engineering Manager — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply` (**false apply**)

## Blocked / ATS notes
- None blocked. LinkedIn SCRAPPING jobs often `linkedin_no_easy_apply`; Capgemini SuccessFactors timed out under ATS cap.

## False applies / code fix
- Capgemini **SAPBTP** redirect passed because skills laundry listed `.NET` while title had none → require `.NET` on **title** for SAP/SAPBTP redirects.
- Cyient **Manufacturing Engineering Manager** passed via Arch/Lead EM exception → skip manufacturing/ops EM titles without `.NET` on title (+ `manufacturing` in non-software keyword list).
- Merged https://github.com/rafi-solibri/MyRepo/pull/266. Post-fix re-run: **450 → 450** (+0); both false-apply titles correctly skipped (`SAP without .NET` / `ops/manufacturing EM without .NET on title`).

## Top 3 LinkedIn referral drafts
- **Globallogic India / Senior .NET Lead (Principal Engineer) IRC296129:** Hi — I'm applying for Senior .NET Lead (Principal Engineer) IRC296129 at Globallogic India. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **Capgemini / PU1 Support- Architect - Offshore Manager:** Hi — I'm applying for PU1 Support- Architect - Offshore Manager at Capgemini. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **blackbaud india / Software Engineer, Principal - .NET Developer:** Hi — I'm applying for Software Engineer, Principal - .NET Developer at blackbaud india. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-26/foundit-apply-report.json`)
