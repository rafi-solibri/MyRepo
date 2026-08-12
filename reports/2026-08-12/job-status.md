# Job status — 2026-08-12

Cloud batch run of all job-apply automations (manual trigger). Targets: Expected CTC 65 LPA · Hyd + Remote/WFH · `Rafi_Resume.docx`.

## Totals by portal

| Portal | Applied | External | Blocked | Skipped | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| LinkedIn | 35 | 0 | 27 | ~226 | Easy Apply daily limit hit |
| Indeed | 9 | 0 | 2 | 27 | WARP+UC preflight OK; 8 incomplete/rejected |
| Instahyre | 3 | 0 | 0 | 677 | Incl. Uber Senior Staff Engineer |
| Foundit | 1 | 0 | 0 | 508 | Aveva Falcon OK; Workday login wall (owner) |
| Cutshort | 1 | 0 | 0 | — | 323 locked-empty questionnaires (historical) |
| Naukri | 0 | 0 | 1 | 2483 | STEP 0 profileUpdated=true; inventory depleted |
| Hitech City | 0 | 0 | 23 | 225 | reCAPTCHA / Amazon login (owner) |
| **Total confirmed applies** | **49** | | | | |

Home-local same-day JSON: not used for this cloud batch (reports from portal agent runs / `reports/2026-08-12/`).

## Highlights
- LinkedIn: 35 Easy Applies (ANSR, Evernorth, aha, Backbase, TTEC, …) then daily limit.
- Indeed: 9 Easy Applies (Innobiz, Recruise, JUARA, Fairground, Acads360×2, SmartDocs, Hire3global, Hire3 Labs).
- Instahyre: Intellect Design Arena, Nineleaps, Uber.
- Foundit: Aveva Senior Consultant (Falcon); Workday Create Account wall needs owner login.
- Cutshort: Firmware Lead @ Gradera AI Technologies.
- Naukri: resume refreshed “Uploaded today”; Apple SRE EM blocked on ATS login/captcha.
- Hitech City: no confirmed submits; LinkedIn/Qualcomm reCAPTCHA + Amazon passport walls.

## Fix PRs merged today
- #95 Instahyre opportunities feed
- #96 Foundit seniority + Workday handoff
- #97 Cutshort C# filter
- #98 Naukri company-site CTA
- #99 Indeed reCAPTCHA/Review CTA
- #100 LinkedIn search-list + HTTP retries
- #101 Hitech City CAPTCHA bail / EXT caps / loc filters

## Owner actions
- Aveva Workday account (Foundit)
- Apple jobs.apple.com login/captcha (Naukri)
- LinkedIn/Qualcomm reCAPTCHA + Amazon login (Hitech City)
- Optional CapSolver/2Captcha for Indeed review reCAPTCHA
- Set `RESEND_FROM_EMAIL` to a verified sender (sent via onboarding@resend.dev fallback)
