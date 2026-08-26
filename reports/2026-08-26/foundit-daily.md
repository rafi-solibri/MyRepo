# Foundit daily — 2026-08-26

## Morning cron (pre-ATS-complete fix)

- Login: MSSOAT + jwtOk=True; hiRafi confirmed (`wait_for_cdp_login.js`).
- Applied tab: **445 → 450** (+5). Intentional logged: **5**. Age → **3650d**.
- Candidates: d1=49 / d3=167 / d7=258 / d14=300 / d30=270 / d90=192 / d3650=38.
- Skips: 1197 | duplicates: 72 | blocked: 0.
- No `canJobApply` dry-run.
- Resume: `resumes/Rafi_Resume.docx` with per-apply JD tailor + profile upload.

### Applied (Falcon redirect only — later treated as NOT confirmed)
1. Globallogic India — Senior .NET Lead (Principal Engineer) IRC296129 — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
2. Capgemini — PU1 Support- Architect - Offshore Manager — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `external_incomplete_or_timeout` (SuccessFactors/SAPBTP) (**false apply**)
3. blackbaud india — Software Engineer, Principal - .NET Developer — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
4. Blue Yonder — Sr Enterprise Technical Architect (Planning) - GPTS Consulting — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply`
5. Cyient — Manufacturing Engineering Manager — Falcon `APPLY_REDIRECT_STAGE_ONE` / ATS `linkedin_no_easy_apply` (**false apply**)

### Filter fix (PR 266)
- Capgemini **SAPBTP** redirect passed because skills laundry listed `.NET` while title had none → require `.NET` on **title** for SAP/SAPBTP redirects.
- Cyient **Manufacturing Engineering Manager** passed via Arch/Lead EM exception → skip manufacturing/ops EM titles without `.NET` on title.
- Merged https://github.com/rafi-solibri/MyRepo/pull/266. Post-fix re-run: **450 → 450** (+0); both false-apply titles correctly skipped.

## Post-fix re-run on merged PR 272 (ATS-complete count)

Ran `POST_FIX_RERUN=1` on `main` @ `e825b109` (`fix: require ATS complete for Foundit; cloud-only notification; Google 2FA chat (#272)`).

- Preflight: `Rafi_Resume.docx` rebuilt from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx`; Foundit cookies `MSSOAT` synced; Chrome CDP `/home/ubuntu/.config/chrome-foundit`.
- Login: MSSOAT + jwtOk=True; hiRafi false (`Hi, Seeker` placeholder) but cookie + onApp OK (`wait_for_cdp_login.js`).
- Applied tab: **453 → 453** (+0). Intentional logged: **0** (only `linkedin_easy_apply_ok` / `ats_submitted` count).
- Candidates: d1=45 / d3=182 / d7=266 / d14=285 / d30=256 / d90=193 / d3650=46. Age → **3650d**.
- Skips: 1198 | duplicates: 75 (all `userJobInfo` — already applied, including this morning’s Falcon redirects) | blocked: 0.
- No `canJobApply` dry-run. No invented applies.
- Remaining Hyd/remote Arch/Lead/.NET inventory was already on the Applied tab. Other .NET Architect/Lead hits were Bangalore/Pune/Noida/Singapore/low-CTC/junior-band skips (correct).

### Confirmed applies this re-run
None. Falcon `APPLY_REDIRECT` + LinkedIn-without-Easy-Apply is no longer counted.

### Blocked / ATS notes
None this pass (eligible leftovers were duplicates, not new ATS handoffs).

### Top 3 LinkedIn referral drafts
No new confirmed applies — drafts only for this morning’s real .NET-fit roles (not the false applies):

- **Globallogic India / Senior .NET Lead (Principal Engineer) IRC296129:** Hi — I'm applying for Senior .NET Lead (Principal Engineer) IRC296129 at Globallogic India. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **blackbaud india / Software Engineer, Principal - .NET Developer:** Hi — I'm applying for Software Engineer, Principal - .NET Developer at blackbaud india. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **Blue Yonder / Sr Enterprise Technical Architect (Planning) - GPTS Consulting:** Hi — I'm applying for Sr Enterprise Technical Architect (Planning) at Blue Yonder. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)

Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-26/foundit-apply-report.json`)
Agent: https://cursor.com/agents/bc-f37b7d51-d27e-43cf-a1af-86ea10e5472a
Merged code: https://github.com/rafi-solibri/MyRepo/pull/272
