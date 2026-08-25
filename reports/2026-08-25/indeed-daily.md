# Indeed daily — 2026-08-25 (post-fix re-run)

Same-day re-run after #257 (`scripts/sync-chrome-sessions.sh` hirist DEST/cookie arrays) so today's applies used merged `main`.  
`POST_FIX_RERUN=1`. Date=2026-08-25 IST.

Source: cloud WARP + SeleniumBase UC (`cloud-warp-uc`)  
Resume: `resumes/Rafi_Resume.docx` (JD-tailored per apply; Expected 65 LPA / Current 52 LPA; Hyd + Remote)

Agent: https://cursor.com/agents/bc-c5abfb31-d385-41e4-a51c-b20f09ce7278

## Totals

| Metric | Count |
| --- | ---: |
| Applied (Easy Apply submitted) | **7** |
| External ATS completed | 0 |
| Rejected / incomplete | 9 |
| Blocked | 18 |
| Skipped | 50 |
| Seen | 84 |

Preflight: WARP SOCKS + UC Turnstile (`uc_gui_click_cf_retry`) → **exit 0** (`uc_bypass_cleared`).  
Session restore: Passport cookies + `secure.indeed.com/settings/account` → signed in.  
`daily_apply.js` / `uc_daily_apply.py` **exit 0**. No invented applies. Already-applied today skipped (25).

## Applied (Easy Apply)

1. **Genpact India Pvt. Ltd.** — Architect - Enterprise Application - Oracle N 4D — Hyderabad (`jk=6144ccb606d68e34`)
2. **Genpact India Pvt. Ltd.** — Senior Principal Consultant - Cloud Solution Architects — Hyderabad (`jk=88c15aca14c7f524`)
3. **Genpact India Pvt. Ltd.** — Architect - Application Development Microsoft N 4D — Hyderabad (`jk=9a3d016a76c03e96`)
4. **PepsiCo** — Cloud Assoc Principal Engineer — Hyderabad (`jk=ad3f66a161f008e3`)
5. **Lntechsystem Private Limited** — Sr. FDE (Resident Solution Architect) – Databricks — Remote (`jk=4d7199bd6ccc1293`)
6. **TECH NEXT** — AI Solution Architect — Remote (`jk=6fdbfeac1614f649`)
7. **Revolite Infotech Pvt. Ltd** — Analytics Solutions Architect — Remote (`jk=e386489be34cc5a8`)

## Skipped

- **already_applied:** 25 (Hyd/.NET architect & lead inventory already on file)
- **title_not_target:** 21
- **location:** 3 (Noida / Kerala / non-Hyd without remote)
- **title_skip:** 1 (Salesforce CRM primary)

## Rejected / incomplete (Easy Apply questions)

Stuck on `questions-module/questions/1` (not invented as applied):

| Company | Title | First unanswered cue |
| --- | --- | --- |
| WSA APAC | Senior Platform Architect | expected CTC left empty after current CTC=52 |
| ValGenesis | Senior Software Engineer, Fullstack | India - Standard combobox |
| LTIMindtree | Senior Principal - Architecture | Title Mr/Ms |
| LTM | Principal / Specialist - Architecture | Title Mr/Ms |
| ValGenesis | Senior Software Engineer, Database | India - Standard |
| UST | .Net Fullstack Developer / Architect I Bengaluru | SmartApply validation |
| Archetype | Senior Software Engineer - .NET | SmartApply validation |

## Blocked

- **no_ats_form (4):** EPAM, BytesEdge, Lexicon, Acuity — brochure / no guest form
- **external_incomplete_or_timeout (6):** Profitics, Clean Harbors (Indeed OAuth “Unreviewed app”), Pennywise, Impelsys, Marx, Infopine
- **ats SOCKS fail (4):** DocOnline, MNJ Software ×2, Core Value — Playwright `net::ERR_SOCKS_CONNECTION_FAILED` through WARP
- **did_not_leave_indeed (1):** NTT DATA applystart hop
- **job_unavailable (1):** IConnectIT
- **easy_apply_recaptcha (2):** Technology Next Agentic AI; Prahartech Principal AI — capped, continued

Late SERP cards hit `from=bot-detection-anonymous` Sign-in (classified title_not_target, not counted as applied).

## Artifacts

- `/opt/cursor/artifacts/indeed-daily-run.json`
- `/opt/cursor/artifacts/indeed-apply-report.json`
- `/opt/cursor/artifacts/indeed-preflight.json`
- `/opt/cursor/artifacts/indeed-cf-bypass.png`
- `/opt/cursor/artifacts/indeed-questions-stuck.png` (WSA APAC expected CTC)
