# Indeed daily — 2026-08-16 (post-fix re-run)

Automation: https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441  
This run: https://cursor.com/agents/bc-164dcdd8-647f-43e0-adb6-79d86f8dca22  
`POST_FIX_RERUN=1` on `main` @ `39cc3e9` (#198), then helper fixes on `cursor/indeed-fix-smartapply-state-already-a239`.

## Preflight
- WARP SOCKS `127.0.0.1:40000` + SeleniumBase UC Turnstile: **cleared** (exit 0)
- Session: Passport cookies present; restored via `secure.indeed.com/settings/account`
- Resume: `/workspace/resumes/Rafi_Resume.docx`

## Counts
| applied (Easy Apply) | external (ATS confirmed) | rejected | blocked | skipped | seen |
| ---: | ---: | ---: | ---: | ---: | ---: |
| **4** | **1** | 12 | 28 | 40 | 83 |

Source: `/opt/cursor/artifacts/indeed-daily-run.json` (`cloud-warp-uc`, 04:11–05:15 UTC).  
`daily_apply.js` exit **0**. No invented applies.

## Submitted
| Path | Role | Company | Location | URL |
| --- | --- | --- | --- | --- |
| Easy Apply | Senior Principal Engineer | AlphaSense India | Remote (in.indeed.com) | https://in.indeed.com/viewjob?jk=6539e734e1b7f0d7 |
| Easy Apply | Staff Platform Engineer | Loti AI | Remote (in.indeed.com) | https://in.indeed.com/viewjob?jk=ce91ec9b52e48ebd |
| Easy Apply | Principal Engineer, Nodejs | Nagarro | Remote (in.indeed.com) | https://in.indeed.com/viewjob?jk=bb7a501c5d902137 |
| Easy Apply | .Net Lead/Senior Software Engineer | Impelsys | **Bangalore / LATAM Remote** (filter miss) | https://impelsys.com/jobs/net-lead-senior-software-engineer/ |
| Company ATS | Senior Application Architect | NTT Ltd | Hyderabad, Telangana | https://in.indeed.com/viewjob?jk=80e5e216f1e2be2f |

Impelsys should have been skipped (Location HARD). Fix on the feature branch: skip LATAM/US/UK/EU remote unless Hyd/India is also present.

## Rejected (Easy Apply incomplete)
- **Already applied** (job-view still showed Apply; SmartApply said already applied) — 5: QualMinds .NET Technical Architect + C#.NET SSE; Gradera Lead .NET Full Stack; Hire3global Engineering Manager; Accellor Backend Tech Lead. Helper now classifies these as skip, not reject.
- **Questions stuck** — 6: ProArch FHIR; UST .Net Fullstack; ValGenesis Fullstack + Database; LTIMindtree Senior Principal (required **PAN** + State unselected); ORBCOMM Zuora Architect.
- **Other** — 1: NTT Phenom apply form mid-flow (same R-125277 as the confirmed ATS).

## Blocked
- Company ATS timeout / no form / SOCKS fail: 22
- Search CF: 2 queries (`Technical Architect C#`, `Technical Lead .NET` Hyd)
- Company CAPTCHA/bot wall: 2
- Job unavailable: 1
- Easy Apply reCAPTCHA on review: Syndigo/Riversand PIM Solution Architect (`jk=4746b61c74568145`)

## Skipped
title_not_target 33 · location 4 · no_apply_button 2 · title_skip 1 (Commerce Cloud)

## Helper fixes (this run)
Branch `cursor/indeed-fix-smartapply-state-already-a239`:
1. Detect SmartApply “You have already applied” as skip (do not count as rejected / submitted).
2. Fill **State = Telangana** on SmartApply questions.
3. Skip required PAN/Aadhaar (`government_id_required`) — do not invent IDs.
4. Skip foreign Remote (LATAM/US/UK/EU) without Hyd/India.

Late inventory hit Indeed Sign-in pages (session flake after ~80 seen). Residual CF/reCAPTCHA still needs home Wi‑Fi or residential `INDEED_HTTP_PROXY` for review submits.
