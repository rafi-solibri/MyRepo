# Indeed daily — 2026-08-17 (post-fix re-run)

Source: cloud WARP + SeleniumBase UC (`cloud-warp-uc`)  
`POST_FIX_RERUN=1` on `main` at `acf04ea` (includes merged #206).  
Resume: `resumes/Rafi_Resume.docx` (Expected 65 LPA / Current 52 LPA; Hyd + Remote)

Automation: https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441  
This run: https://cursor.com/agents/bc-dcc00799-5c6b-4aae-ba42-16d583503c9d

## Totals

| Metric | Count |
| --- | ---: |
| Applied (Easy Apply submitted) | 1 |
| External ATS completed | 0 |
| Rejected / incomplete | 8 |
| Blocked | 23 |
| Skipped | 50 |
| Seen | 82 |

Preflight: WARP SOCKS + UC Turnstile clear → **exit 0** (`uc_bypass_cleared`).  
Session: Passport auth cookies present; signed in via Account settings.

`ok: true` — at least one confirmed Easy Apply. No invented applies.

## Applied (Easy Apply)

1. **Teradata** — Principal Engineer — Hyderabad  
   https://in.indeed.com/viewjob?jk=2da2dbb69fc32e62

## Skipped already applied today (8)

Did not re-apply:

- QualMinds — Solution Architect
- QualMinds — .NET Technical Architect
- QualMinds — Senior Software Engineer - C#.NET
- Gradera — Lead .NET Full Stack Engineer
- Techno-Comp — Senior Technical Architect (Medchal)
- Recruise — 6041_Technical Lead (.Net)
- Accellor — Backend Tech Lead
- Aapmor — Technical Lead

## Rejected / incomplete Easy Apply (8)

Stuck on SmartApply `questions-module/questions/1` (required employer fields: Title/Mr-Ms, phone/DOB, preferred location, contact). Not counted as applied.

- ProArch — Senior .Net Core Developer with FHIR
- ValGenesis — Senior Software Engineer, Fullstack
- UST — .Net Fullstack Developer
- Cognizant — Principal Architect (landed on careers.cognizant.com)
- LTIMindtree — Senior Principal - Architecture
- ORBCOMM — Zuora Architect
- LTM — Principal - Architecture
- ValGenesis — Senior Software Engineer, Database

## Blocked (23)

- **external_incomplete_or_timeout (14)** — company ATS hit the 390s cap (Absyz Salesforce careers drifted to a CPQ listing; Greenhouse Arcesium; Gaian; CGLIA; GLOINNT; WeSquare; others). No confirmation → not applied.
- **no_ats_form (6)** — brochure / careers listing with no guest form (BytesEdge, Lexicon, Cognizant listing, Infovity, Vidyavision).
- **CAPTCHA/bot wall (2)** — AppsTek, Swayam Group. Owner/residential only.
- **job_unavailable (1)** — QualiZeal Data Architect.

## Other skips

- title_not_target: 37 (no senior/architect/lead/.NET signal, or Sign-in SERP cards on later queries)
- no_apply_button: 2
- location: 2 (Kerala; Bengaluru)
- title_skip: 1 (Salesforce/ServiceNow-primary title)

Late search queries opened `Sign In | Indeed Accounts` cards (session chrome, not job pages) and were title-skipped. Inventory still ran through 11 homepage searches / 82 seen.

## Artifacts

- `/opt/cursor/artifacts/indeed-daily-run.json`
- `/opt/cursor/artifacts/indeed-apply-report.json`
- `/opt/cursor/artifacts/indeed-preflight.json`
- `/opt/cursor/artifacts/indeed-cf-bypass.png`
