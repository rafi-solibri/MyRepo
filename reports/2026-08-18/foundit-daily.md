# Foundit daily — 2026-08-18 (post-fix re-run)

SAME-DAY POST-FIX RE-RUN. `POST_FIX_RERUN=1`. Ran on merged `main` (`46012f5`, including `fix(ats): import os in persist_retry path` #208). Earlier IST cron did not apply with that fix.

## Summary
- Logged in: **yes** (MSSOAT + jwtOk + `/seeker/dashboard`; greeting stayed "Hi, Seeker")
- Applied tab: **490 → 497** (+7). Intentional logged: **6**
- Skipped: 1188 · Duplicates: 70 · Blocked: 0
- Age window: → **3650d**. Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- Resume: `resumes/Rafi_Resume.docx`

## Applied
1. CareerXperts Consulting — Senior Dotnet Developer — Foundit Falcon (`63072569`)
2. Globallogic Ukraine — Senior .NET Lead (Principal Engineer) IRC296129 — Falcon + LinkedIn `4440673109` (`linkedin_no_easy_apply`)
3. Jobgether — Senior Integration Developer/ Architect — Falcon + LinkedIn `4453578310` (`linkedin_no_easy_apply`)
4. Accenture — Technology Architect — Falcon + `monsterindia.com/event/triumph/` → `foundit.in/event/triumph/` (`external_incomplete_or_timeout`)
5. tylsemi — Principal Engineer - SoC RTL Design — Falcon + LinkedIn `4445627448` (`linkedin_login_wall`) — **false apply** (silicon/RTL Arch without .NET) → filter fix same day
6. locaxion — Senior Software Architect — Falcon + LinkedIn `4352531032` (`linkedin_no_easy_apply`)

No invented applies. Jobs already on the Applied tab were skipped via `userJobInfo` / `applicationStatus` (70 duplicates). `canJobApply` was not used.

## Top skip reasons
- location not Hyd/remote (552)
- no .NET on title+skills (355)
- no seniority / junior-mid exp bands / SAP / non-software / infra / pure AI

## Code fix this run
1. Hard-skip `SoC|ASIC|RTL design|silicon|semiconductor|FPGA|Verilog|VHDL` titles without `.NET` on the title so Arch/Lead cannot false-apply chip/hardware Principal roles (LinkedIn parity). Tests `26.3` / `26.4`.
2. Fail-fast Foundit/Monster `/event` URLs (`foundit_event_not_ats`) and prune Access Denied tabs so event/triumph pages cannot burn the 6.5m ATS cap.

## LinkedIn referral drafts
1. **CareerXperts Consulting / Senior Dotnet Developer** — Hi — I'm applying for Senior Dotnet Developer at CareerXperts Consulting. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
2. **Globallogic Ukraine / Senior .NET Lead (Principal Engineer) IRC296129** — Hi — I'm applying for Senior .NET Lead (Principal Engineer) IRC296129 at Globallogic Ukraine. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
3. **Jobgether / Senior Integration Developer/ Architect** — Hi — I'm applying for Senior Integration Developer/ Architect at Jobgether. 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA. Happy to share Rafi_Resume.docx — could you refer me to the hiring manager? Thanks, Rafi Ahmed ([REDACTED] / +91 8790251698)
