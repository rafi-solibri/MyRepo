# Daily apply — 2026-08-23 (post-fix re-run)

## Status
**COMPLETE** for this IST day. Confirmed submits only — nothing invented.

This is post-fix re-run **#2** of 5 after merged #244 (master resume). Easy Apply used the font-stripped `Rafi_Resume.docx` (~15KB) under the 2MB cap. Company-site / ATS pass ran on the same CDP session and skipped the 34 IDs already submitted earlier today.

## Totals (confirmed)
| Path | First run (bc-902b0e1a) | This pass | Day total |
| --- | ---: | ---: | ---: |
| Easy Apply submitted | 22 | **11** | **33** |
| Company-site / ATS submitted | 1 | **1** | **2** |
| **Confirmed total** | 23 | **12** | **35** |
| Easy Apply blocked (time-cap) | 9 | 4 | 13 |
| ATS blocked | — | 28 | 28 |
| Easy Apply skipped (this pass) | — | 470 | — |

## This-pass Easy Apply (11)
| Company | Role | Job ID | Location |
| --- | --- | --- | --- |
| Blue Spire Inc | Calypso Dotnet Developer | 4456186232 | Hyderabad |
| Cotiviti | Technical Architect | 4445725127 | Hyderabad |
| Canterr, Inc. | Staff Back-End Engineer | 4456807075 | Hyderabad |
| Luxoft | Senior Fullstack developer (.NET+Angular) | 4457364602 | Hyderabad |
| Liquidnitro Games | Lead Software Engineer | 4446601488 | Hyderabad |
| Credera | Senior Architect | 4407801132 | Hyderabad |
| Quadrant IT Services | Sr Architect | 4455300193 | Hyderabad |
| Solugenix | Software Architect | 4456446846 | Hyderabad |
| GSPANN Technologies, Inc | Datadog Architect | 4456725146 | Hyderabad |
| Emburse | Staff Engineer I (Node.JS) | 4445956282 | Hyderabad |
| Sumanjali landscape architects | Architect | 4451705902 | Hyderabad |

## This-pass ATS (1)
| Company | Role | Job ID | Confirmation |
| --- | --- | --- | --- |
| NTT DATA, Inc. | Public Cloud Architect | 4409290239 | ATS confirmation |

Morning ATS NTT DATA Senior Application Architect `4409294028` is a different job (already in the first-run 23).

## False-allow
- **Sumanjali `4451705902`**: title “Architect”, company is a landscape-architecture firm. Logged because the helper recorded Application submitted. Filter now rejects `landscape architect` on title or company. Do not treat this as a software callback.

## This-pass Easy Apply blocked (time-cap)
| Company | Role | Job ID |
| --- | --- | --- |
| Blend | AI Engineering Lead - Agentic Engineering | 4457897557 |
| Sonatype | Staff Full Stack Software Engineer | 4452938002 |
| TalentXO | Senior Python Architect (AWS) | 4457310783 |
| Aarushi Infotech | Senior Business Architect – Telecom Domains | 4454991685 |

Coforge `4453428680` and the first Blue Spire attempt also hit the step cap; Blue Spire later submitted.

## This-pass ATS outcomes
- Submitted: **1** (NTT DATA `4409290239`)
- Blocked **28**: 16 timeout / incomplete form, 6 ATS login wall, 5 captcha / bot wall, 1 did not leave the job host
- Skipped **11**: 8 became Easy Apply, 3 no ATS form
- Already-applied skip set: **34** IDs (first-run 23 + this-pass 11 Easy Apply)

Notable ATS blocks (not submits): Palo Alto / Solera / AVEVA / SimCorp login wall; Hyland / Brady / Kidde / Rise captcha; Workday timeouts (GE Vernova, Cognizant, insightsoftware, RSM, FedEx, Infosys).

## First-run confirmed (22 Easy Apply + 1 ATS)
NCompas 4455650102, Ibexlabs 4454970033, Teradata 4454236005, Mulya 4455277149, BlitzenX 4455049038, Chubb 4457591813, CareerXperts 4454600085, ShimentoX 4457097946, Talent500 4455266108, Teradata 4437991428, Deutsche Börse 4457305150, WillWare 4457087275, TCS APex 4456693953, ginfracon 4451200625, Deutsche Börse 4453457452, Talent500 4455257744, Mulya STA 4455279550, TCS Coveo 4455234873, Chubb SRE 4455577581, Tech Mahindra 4443251675, Kanerika QE 4454240217, Arcesium 4456700256, **NTT DATA ATS 4409294028**.

Several of those first-run titles (shop-floor, STA/DFT, QE, Data&AI/Databricks, SRE) are now title-blacklisted so they will not be re-applied.

## Fixes on this branch
- Title filters: shop-floor, STA/DFT, QE, Data&AI/Databricks, junior/BIM, SRE
- Seed today’s already-applied IDs
- Restore newer seed session + complete Google identifier SSO
- Shrink Easy Apply resume under 2MB (strip embedded fonts)
- Skip already-submitted IDs in the company-site pass
- Skip landscape-architecture “Architect” cards (Sumanjali)

## Artifacts
- `/opt/cursor/artifacts/apply-report.json` (this-pass Easy Apply)
- `/opt/cursor/artifacts/external-apply-report.json` (ATS)
- Helper logs under `/opt/cursor/artifacts/` (Easy Apply + company-site)
- Screenshots: `submitted-{id}.png` / `ext-submitted-4409290239.png`

## Notification
This file is the confirmed source for the 2026-08-23 jobs portal line. Other portals are not claimed here.
