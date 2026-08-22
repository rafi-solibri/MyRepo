# Foundit daily — 2026-08-22

- Login: MSSOAT + jwtOk=True; hiRafi via wait_for_cdp_login.
- Applied tab: **441 → 455** (+14). Intentional logged: **14**. Age → **3650d**.
- Skips: 1181 | duplicates: 65 | blocked: 1.
- No `canJobApply` dry-run.

## Applied
1. Numerator — Senior Software Engineer — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `ats_error`
   - path: Foundit + ATS https://recruit.hirebridge.com/v3/careercenter/v2/details.aspx?jid=610381&cid=7844&locvalue=1112&bid=10
2. Numerator — Senior Full Stack Developer — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://recruit.hirebridge.com/v3/careercenter/v2/details.aspx?jid=611339&cid=7844&locvalue=1112&bid=10
3. Infosys Limited — .Net angular Lead — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://career.infosys.com/jobdesc?jobReferenceCode=INFSYS-EXTERNAL-247841
4. Infosys Limited — .Net production support Lead — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://career.infosys.com/jobdesc?jobReferenceCode=INFSYS-EXTERNAL-247850
5. Hitachi Energy — Data Services - Solution Architect — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `ats_login_wall`
   - path: Foundit + ATS https://hitachi.wd1.myworkdayjobs.com/en-US/hitachi/job/Krakow-Lesser-Poland-Poland/IT-Data-Governance-Expert_R0115743
6. Microsoft Corp — Solution Architect Manager — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
   - path: Foundit + ATS https://www.linkedin.com/jobs/view/4456300501/
7. Infosys Limited — Senior Global Deal Solution Architect (GCCCOE - JL7) — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://career.infosys.com/jobdesc?jobReferenceCode=INFSYS-EXTERNAL-249369
8. Infosys Limited — Lead Technical Architect Modern C Plus and Enterprise Systems — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://career.infosys.com/jobdesc?jobReferenceCode=INFSYS-EXTERNAL-249569
9. Infosys Limited — UI Technical Architect React and Angular — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://career.infosys.com/jobdesc?jobReferenceCode=INFSYS-EXTERNAL-249556
10. Capgemini — Principal Software Engineer — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://www.capgemini.com/in-en/jobs/465333-en_GB_SAPBTP/Principal%20Software%20Engineer
11. The Ksquare Group — Application Architect — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
   - path: Foundit + ATS https://www.linkedin.com/jobs/view/4450454590/
12. Hitachi Energy — Engineering Manager DTT — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `ats_login_wall`
   - path: Foundit + ATS https://hitachi.wd1.myworkdayjobs.com/en-US/hitachi/job/Maneja-Gujarat-India/Engineering-Manager-DTT_R0109205
13. S&P Global Market Intelligence — Software Engineering Manager, Backend Development (Python) — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://careers.spglobal.com/jobs/323133?lang=en-us
14. Aveva — R&D Principal Technologist — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout`
   - path: Foundit + ATS https://aveva.wd3.myworkdayjobs.com/en-US/AVEVA_careers/job/Hyderabad-India/R-D-Principal-Technologist_R012502

## Blocked / ATS notes
- Senior Software Engineer: ats_error — Error: page.goto: net::ERR_HTTP_RESPONSE_CODE_FAILURE at https://recruit.hirebridge.com/v3/careercenter/v2/details.aspx?jid=610381&cid=7844&locvalue=1112&bid=10

## False applies / code fix
- S&P Global Python EM, Infosys “C Plus” Arch, Capgemini SAPBTP Principal → fixed in `tools/foundit/filters.js` (NON_DOTNET_PRIMARY title parity + SAPBTP redirect).

## Top 3 LinkedIn referral drafts
- **Numerator / Senior Software Engineer:** Hi — I'm applying for Senior Software Engineer at Numerator. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **Numerator / Senior Full Stack Developer:** Hi — I'm applying for Senior Full Stack Developer at Numerator. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)
- **Infosys Limited / .Net angular Lead:** Hi — I'm applying for .Net angular Lead at Infosys Limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed (rafi.success@gmail.com / +91 8790251698)

Artifact (morning): `/opt/cursor/artifacts/foundit-apply-report.json`

## Post-fix re-run (cloud, POST_FIX_RERUN=1, merged main)

Re-executed `node tools/foundit/daily_apply.js` on `origin/main` at `0cfa954` (includes Foundit filter [#233](https://github.com/rafi-solibri/MyRepo/pull/233) and later [#234](https://github.com/rafi-solibri/MyRepo/pull/234)). Resume: `resumes/Rafi_Resume.docx`. Login OK (MSSOAT + jwtOk). No `canJobApply` dry-run. No invented applies.

- Applied tab: **456 → 456** (+0). Intentional logged: **0**. Age → **3650d**.
- Skips: 1185 | duplicates: 76 (all `userJobInfo`) | blocked: 0.
- New LinkedIn referral drafts this re-run: none (no new applies).

Morning applies skipped as already submitted (sample): Numerator 63554913/63554914, Infosys .NET leads 63645819/63646669/63628577/63634239, Hitachi 63572353, Microsoft 63639577, Ksquare 63640361, Aveva 40462478.

[#233](https://github.com/rafi-solibri/MyRepo/pull/233) filter confirmation (not re-applied):
- Infosys 63631709 Lead Technical Architect Modern C Plus → skip `no .NET on title+skills`
- Capgemini 63613636 Principal Software Engineer (SAPBTP URL) → skip `SAP without .NET`
- S&P 39914436 Software Engineering Manager, Backend Development (Python) → skip `no .NET on title+skills`
- Also skipped Mainframe titles via new `non-.NET primary stack on title`

No new code-fixable blocker. Did not launch another post-fix re-run.

Artifact (this re-run): `/opt/cursor/artifacts/foundit-apply-report.json`
