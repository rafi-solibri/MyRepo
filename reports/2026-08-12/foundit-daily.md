# Foundit daily 2026-08-12

## Counts
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (after confirmLogin harden)
- Applied tab: **455 → 458** (+3)
- Intentional applies: **3**
- Duplicates (`userJobInfo`): **32**
- Skipped: **510** (location 172 / no .NET 150 / no seniority 129 / junior-mid / CTC / other)
- Blocked: **0**
- Age window used: **3650d** (expanded after thin fresh Hyd/remote senior .NET inventory)
- Resume: `resumes/Rafi_Resume.docx`
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` calls

## Applied
1. embrace software inc — Lead Engineer/ Architect (.NET) - Industrial — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` → LinkedIn `4451558712` (`linkedin_no_easy_apply`) — remote
2. embrace software inc — Tech Lead (.NET) — Foundit Falcon → LinkedIn `4448783234` (`linkedin_no_easy_apply`) — remote
3. Globallogic India — Senior .NET Lead (Principal Engineer) IRC296130 — Foundit Falcon → LinkedIn `4451191928` (`linkedin_no_easy_apply`) — Hyderabad

## Blocked / owner
- None this run (MSSOAT OK). LinkedIn Easy Apply unavailable on SCRAPPING redirects (expected).

## Code fixes shipped
- #79 `chrome_session.js`: restore JS `function checkPortal` (preflight SyntaxError)
- `resolve-python.sh` unset `LOCALAPPDATA` under `set -u` (merged via parallel Instahyre fix on main)
- #87 `daily_apply.js` `confirmLogin`: poll dashboard + `/home/user` fallback (ignore transient `Hi, Seeker`)

## Top 3 LinkedIn referral drafts
1. embrace / Lead Engineer/ Architect (.NET) - Industrial — ask for HM referral; 52→65 LPA, immediate, Rafi_Resume.docx
2. embrace / Tech Lead (.NET) — same
3. Globallogic / Senior .NET Lead (Principal Engineer) IRC296130 — same
