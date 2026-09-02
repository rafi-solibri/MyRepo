# Easy Apply daily — 2026-09-02 IST

**Portal:** Easy Apply + external ATS  
**Candidate:** Mohammed Abdul Rafi Ahmed (Rafi Ahmed)  
**Resume:** `resumes/Rafi_Resume.docx` (rebuilt from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx`, 20945 B)  
**Locations:** Hyderabad + Remote India (`f_WT=2`) only  
**People-referrals:** OFF  
**Easy Apply target:** 40–50 (daily Easy Apply limit hit at 12)  
**Confirmed submitted:** **13** (12 Easy Apply + 1 external ATS). Do not invent more.

## Login / session

- Preflight `scripts/preflight-portal-run.sh` passed (`li_at` present in SQLite).
- CDP Chrome launched via `scripts/launch-chrome-cdp.sh` on `:9222` with WARP SOCKS `socks5://127.0.0.1:40000`.
- Live session was **dead** (`/uas/login` despite cookie name). Auto-login ran.
- **ASK_OWNER_GOOGLE_2FA** — Google `/signin/challenge/dp` (phone Tap Yes). Owner approved.
- Login completed via portal password after GSI timeout. Seed refreshed. `GOOGLE_PASSWORD` + portal email/password secrets were present (unlike 2026-09-01).
- No restriction flag.

## Submitted (confirmed Easy Apply — 12)

| # | Company | Role | Job ID | Location | Notes |
|---|---|---|---|---|---|
| 1 | Turing | Remote Software Engineer – C# | 4460957468 | India (Remote) | Easy Apply |
| 2 | HighRadius | Senior Product Solutions Architect | 4449848134 | Hyderabad | Easy Apply |
| 3 | Talent500 | FullStack Developer .net/ Angular (Lead) [T500-28850] | 4458723595 | Hyderabad | Easy Apply |
| 4 | First American (India) | Staff Platform Engineer | 4459931286 | India | Easy Apply after `remote_search` view-location fix |
| 5 | Hutchison Limited, India | Odoo System Architect And Product Owner | 4459937246 | Hyderabad | Easy Apply (stretch: Odoo) |
| 6 | Tata Consultancy Services | Dot net with Angular | 4460950699 | Hyderabad | Easy Apply after TITLE_OK `dot net` fix |
| 7 | Launch India | .Net Full Stack Engineer | 4458205183 | Hyderabad | Easy Apply |
| 8 | E-Solutions | Senior Software Engineer – C++ | 4462158526 | India | Easy Apply (stretch: C++) |
| 9 | CareerXperts Consulting | Technical Lead — .NET, C#, Global SaaS Platform | 4459925722 | Hyderabad | Easy Apply |
| 10 | Allied Globetech | Integration Specialist (.Net) | 4459915436 | Hyderabad | Easy Apply |
| 11 | Jobgether | Databricks Solution Architect-Databricks Champion | 4460214913 | India | Easy Apply (stretch: Databricks) |
| 12 | Stackzy Technologies Pvt Ltd | Windchill Solution Architect | 4460070279 | India | Easy Apply (stretch: Windchill) |

Easy Apply daily limit (`You've reached today's Easy Apply limit`) after #12. Helper stopped Easy Apply and continued non-Easy-Apply search (`easy_apply_daily_limit`).

## Submitted (confirmed external ATS — 1)

| # | Company | Role | Job ID | Location | Notes |
|---|---|---|---|---|---|
| 13 | Clean Harbors | Technical Architect | 4454006996 | Hyderabad | Google Form `alreadyresponded` — helper recorded confirmation |

## Not applied (honest)

Far below the 40–50 Easy Apply target. Causes:

1. **Easy Apply daily limit** after 12 submits. Same-day Easy Apply re-run is not useful.
2. **View-page location false-skips** until mid-run fix: `easy_apply_flow` dropped `remote_search`, so India-remote cards that passed the card filter were skipped on `/jobs/view`. Fixed and pushed (`21db5bd`).
3. **Company chrome treated as location** until mid-run fix: view parse overwrote Hyderabad with “Accenture in India” and skipped Cloud Technical Architect. Fixed (`6cc94ce`).
4. **TITLE_OK misses** for `Dot net`, hyphenated manager titles. Fixed (`21db5bd`, `3255d9d`).
5. **External ATS walls:** Workday login (Palo Alto, ConvaTec, ModMed, Medtronic), Hyland captcha, Microsoft/Amazon/EPAM/Wells Fargo no ATS form, Accenture timeout. External helper: submitted 1, blocked 21, skipped 18.

## AUTO_FIX (this run)

| Commit | Fix |
|---|---|
| `fda8cd9` | Session refresh copies cookies only (not Local State) |
| `21db5bd` | Pass `remote_search` through view location check; TITLE_OK `dot net` + Manager Software Development; skip DFT / Python-primary |
| `6cc94ce` | `looks_like_job_location()` — do not treat company chrome as workplace |
| `3255d9d` | TITLE_OK hyphen/dash manager-software-engineering |
| `8ddce66` | Skip QA Architect and Interior / B.Arch |

Tests: `python3 tools/*/test_filters.py` — pass.

## Artifacts

- Easy Apply waves: `/opt/cursor/artifacts/apply-report-wave1.json`, `apply-report-wave2.json`, `apply-report-wave3.json` (last run also at `apply-report.json`)
- External: `/opt/cursor/artifacts/external-apply-report.json`
- Seen IDs: `/opt/cursor/artifacts/*-seen-ids.json` (508)
- Logs: `/tmp/cursor/*-easy-apply.log`, `-wave2.log`, `-wave3.log`, `/tmp/cursor/*-external-apply.log`

## Follow-ups

- Easy Apply daily limit — do **not** re-run Easy Apply today.
- Merge filter fixes to `main` so tomorrow’s run does not false-skip India-remote / Accenture-style cards.
- High-value leftover externals (not submitted): Accenture Cloud Technical Architect, Microsoft / Amazon / Palo Alto / ConvaTec / ModMed / Hyland / Medtronic / EPAM / Wells Fargo — ATS login/captcha/no-form.
