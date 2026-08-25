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
- **Infosys Limited / .Net production support Lead:** Hi — I'm applying for .Net production support Lead at Infosys Limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **Infosys Limited / .Net angular Lead:** Hi — I'm applying for .Net angular Lead at Infosys Limited. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
- **avalara apac / Senior Software Engineering Manager:** Hi — I'm applying for Senior Software Engineering Manager at avalara apac. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)

Artifact (morning): `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-25/foundit-apply-report.json`)

## Post-fix re-run (POST_FIX_RERUN=1, after #264 ATS Gmail OTP)

Ran on `main` @ `0df8822` (`fix(hitechcity): read ATS email OTPs from Gmail mailbox`). Earlier cron / prior re-runs did **not** apply with this helper. This job did: preflight + Chrome CDP (`chrome-foundit`) + `node tools/foundit/resume.js` + `wait_for_cdp_login.js` + `node tools/foundit/daily_apply.js` (exit 0).

- Login: MSSOAT + jwtOk=True; hiRafi false (Hi, Seeker) but cookie + onApp OK.
- Resume: `resumes/Rafi_Resume.docx` (20,945B rebuilt from owner master). No `canJobApply` dry-run.
- Applied tab: **441 → 441** (+0). Intentional logged: **0**. Age → **3650d**.
- Candidates: d1=144 / d3=72 / d7=326 / d14=239 / d30=283 / d90=174 / d3650=39.
- Skips: 1201 | duplicates: 76 (`userJobInfo`) | blocked: 0.
- No invented applies. Today's morning 12 Falcon submits skipped as already Applied.
- #260 filters still hold (not re-applied):
  - ResultsCX **Sr. Director, Solutions Architect - AI** → `pure AI/data without .NET on title`
  - Infosys **UI Technical Architect React and Angular** → `UI/frontend React/Angular without .NET on title`
  - Jobgether **Senior Technical Lead - Asterisk & Telephony** → `Asterisk/telephony without .NET on title`
- Remaining Hyd/remote Arch/Lead/.NET inventory is already Applied or correctly filter-skipped (Bangalore/Pune/junior/no-seniority/CTC under 35).
- #264 OTP mailbox helper was on the apply path for any new ATS OTP wall; no new Falcon/ATS submit occurred, so Gmail IMAP was not needed this pass (`GMAIL_APP_PASSWORD` unset in this pod — CDP Gmail tab is the fallback if an OTP wall appears).
- This is Foundit post-fix re-run **4/5** for 2026-08-25 IST. No new code-fixable blocker; do not launch another Foundit re-run for this report-only commit.

### Already applied today (skipped — do not re-submit)
Includes morning roles still on the account via `userJobInfo`: Infosys .Net production support Lead / .Net angular Lead / Senior Global Deal SA; avalara SEM; Jobgether Integration SA; Blue Yonder SCPO; realty EM; quik hire Solutions Architect; aarushi OSS Architect.

### Top skip reasons (this re-run)

| Count | Reason |
| --- | --- |
| 361 | no .NET on title+skills |
| 196 | location Bengaluru / Bangalore |
| 112 | no seniority keyword on title |
| 67 | SAP without .NET |
| 42 | location Pune |
| 36 | location Singapore |
| 26 | pure AI/data without .NET on title |

### Referral drafts this re-run
None — 0 new applies (do not invent).

Artifact (this re-run): `/opt/cursor/artifacts/foundit-apply-report.json` (copy: `reports/2026-08-25/foundit-apply-report-postfix.json`)
