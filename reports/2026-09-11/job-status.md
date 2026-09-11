# Job status — 2026-09-11

On-demand cloud status digest (home-local DISABLED). Apply agents launched ~10:53 IST / 05:23 UTC. This run waited until ~08:00 UTC (~2.5h) then sent. Hitech City was still RUNNING; LinkedIn agent resumed after Easy Apply snapshot.

Targets: Expected CTC 65 LPA; Hyderabad + Remote/WFH; resume `Rafi_Resume.docx` (rebuilt each run from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx`, JD-tailored per apply).

**Confirmed totals (ATS / native submit only — no invented applies):** applied **78** · external **0** · rejected **10** · blocked **59+**. Foundit Applied-tab +23 is **not** 23 applies (6 Falcon NORMAL + 17 redirect-only). LinkedIn Easy Apply + Hitech still incomplete.

## Portal results (source: cloud agents, same-day)

| Portal | Applied | External | Rejected | Blocked | Skipped | Seen | OK | Blocker / notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| LinkedIn | 15 | 0 | 0 | 4 | n/a | seed 92 | incomplete | Easy Apply helper still mid-wave; no company-site pass; 4 of 15 are false-applies |
| Foundit | 6 | 0 | 0 | 17 | 1199 | Raven windows | yes | 17 Falcon APPLY_REDIRECT / `external_incomplete` **not applied** |
| Cutshort | 4 | 0 | 0 | 0 | 0* | 3416 | yes | *apply-report skipped=0; filter-skipped thousands (location/title/exp/CTC) |
| Naukri | 15 | 0 | 0 | 13 | 828 | 165 | yes | First-run Quick Apply; postfix 15/30/60 finished with 0 extra |
| Instahyre | 10 | 0 | 0 | 0 | 652 | 662 | yes | Postfix matching-API; interested 367→377 |
| Indeed | 15 | 0 | 10 | 12 | 58 | 95 | yes | Easy Apply finished; Cloudflare cleared; company-site 0 |
| Hirist | 13 | 0 | 0 | 0 | 419 | 432 | yes | Login OK; 4 filter-leak titles still submitted |
| Hitech City / Knowledge City | 0 | 0 | 0 | 13+ | 25+ | 60 co. careers | incomplete | Careers/boards finished 0 applies; LinkedIn looping Micron EXT; no `hitechcity-daily.json` |

Finished (IDLE): Hirist 05:26 UTC · Instahyre ~05:43 · Cutshort 06:20 · Foundit 06:19 · Naukri 07:39 · Indeed 07:42. Still RUNNING at send: Hitech City; LinkedIn agent resumed after 15 Easy Apply snapshot.

## Agent URLs

- LinkedIn: https://cursor.com/agents/bc-9e882473-aeca-4e12-bfa0-15fd85b72d02
- Foundit: https://cursor.com/agents/bc-3a08ba51-fd15-4085-a644-283ff7638734
- Cutshort: https://cursor.com/agents/bc-9f5ceae1-de4e-4fc7-b109-10868a8c8c9a
- Naukri: https://cursor.com/agents/bc-0012833d-a7ff-4c3c-bdd6-22c640bb6dba
- Instahyre: https://cursor.com/agents/bc-8a854c9e-c643-4bc7-9c1e-7f85a9a3942d
- Indeed: https://cursor.com/agents/bc-4e079ace-77bb-42cb-bbcd-a9fe86b59612
- Hirist: https://cursor.com/agents/bc-651d1b37-178c-453a-b3c1-72c3e001aac5
- Hitech City / Knowledge City: https://cursor.com/agents/bc-6d2bd137-759f-4c95-a37e-3ce063c86d40
- This status digest: https://cursor.com/agents/bc-3496c295-5d4f-4b55-a106-6b2d5ed9b7b7

## Highlights (confirmed submits)

### LinkedIn — 15 Easy Apply (`Application submitted` + screenshot). 11 solid / 4 false-apply. External 0 (pass not started). Counts incomplete.

Solid: Talentgigs Technical Lead; Marriott Tech Accelerator SEM FinOps; Astreya Endpoint Management Architect; Simplify Alpha Delivery Architect; Weekday AI Principal Architect (Security) `4465632909`; IndusGuru Cloud Infra & Platform Automation Architect; Sourcebae Solutions Architect; TIGI HR Cloud Architect Azure & AWS; Jobgether EM System Design; Ivycornersearch IT Architect; Weekday Principal Architect (Security) `4463461192` (second listing).

False-apply (submitted anyway): Zigsaw Business Development Manager; Tek Grove Dell Boomi Architect; Sagility Associate Director Training; Latinem Senior Concept Architect (AEC).

Form blocked (not applied): Cyara SEM; Studio Infinite Senior Project Architect; Moniepoint Head of Engineering; HYR ETRM Solution Architect.

Login: Google 2FA owner-approved; restriction already lifted.

### Foundit — 6 Falcon `NORMAL` (native portal). Do **not** count Applied-tab +23.

Twilio Senior Engineering Manager; galaxy weblinks .NET Architect Consultant; TCS Walk-in Azure SA Hyd; TCS Dot NET Full Stack Lead; TCS Azure Solution Architect; TCS AWS Solution Architect.

Redirect-only (17, NOT applied): Ashby/Workday/Appcast/career-page/LinkedIn handoffs (`external_ats_incomplete`). Skip highlights: no .NET 341; Bengaluru loc 206; no seniority 88.

### Cutshort — 4 API applies (`api_no_ui_button`). Qualifying=4, all applied.

AI Architect @ Cutshort Lightning; Principal AI Architect — Multimodal Video Intelligence @ Cutshort Lightning; Agentic Tools Architect @ FAiHr; Tech Lead @ TalentXO.

316 historical `questionnaire_locked_empty` not counted as rejected. Google SSO healed (owner first tapped No, retry OK).

### Naukri — 15 Quick Apply (`chatbot:responses_thanks`) first run (ages 1/3/7). Postfix finished 07:39 UTC with **0 extra**.

Includes several false titles (Fabric / Apigee / Data SA / Oracle Xstore / AI Tech Lead / AEMaaCS / Vue) that still submitted. External 0. Blocked 13: Accenture login walls (3), unconfirmed CTAs (5), ATS timeouts (5). Skipped 828 (mostly duplicate_in_run). Postfix2 blocked 3 more ATS timeouts (Knowbe4, WSA, Medtronic).

### Instahyre — 10 in-app `application_sent`.

Nemetschek TL Fullstack; Helfie.AI Principal Engineer ×2 listings; Happiest Minds Technical Solution Architect WFH; Neve Jewels DevOps Architect; HighLevel Staff Engineer; CBRE Software Engineer Architect; Nineleaps Python Engineer; Soulside AI Backend Engineer; HighLevel SDE III Social Planner.

First pass 0 applies (candidate_opportunity API 404); postfix matching-API recovered all 10. Skip: location_not_hyd_remote 540; already_interested 77.

### Indeed — 15 Easy Apply finished (`ok: true`, 07:42 UTC). Cloudflare 403 cleared; Google 2FA done. Company-site 0.

Prior 11 plus: Orogoo AI / Agentic Solution Architect; Cidroy Infotech Software Architect; Taranta Consultancy Solution Architect; Websenor Senior Solution Architect (all Remote). Also: Nagarro Principal Engineer (Integration Architect); LETITBEX Software Technical Lead + Senior SWE; Health Catalyst SDE; Aarika .NET Tech Lead; akshaya Senior Dot Net Developer; Visionary Staffing Pega LSA; Genpact Technical Architect 4D; TTEC Digital Principal SA AWS; CN Global D365 Technical Architect; Naveera Senior AI/ML Engineer | Lead | Architect.

Rejected 10 (`easy_apply_incomplete`). Blocked 12 (external ATS / no_ats_form / recaptcha). Skip 58 (already_applied 31). Seen 95.

### Hirist — 13 in-app `hirist_apply`. Login OK. Filter leaks still submitted: Teamcenter SA, Workday Recruiting SA, AI/ML EM, Principal Power BI.

Also: Senior ASP.Net MVC / Tech Lead (Acharya); Technical Lead .Net (Anveta); EM .Net (WRTR INK); EM Full Stack (Tidyhire); Security Architect Cloud (Albireo); Lead Developer .Net+Angular (DSRC); AWS Cloud Architect CI/CD (Forward Eye); Technical Architect Banking (iXceed); .Net Full Stack (Growel Softech). Skip: location 249; pure AI/data 66; java 36.

### Hitech City / Knowledge City — 0 confirmed applies (incomplete).

Careers: applied 0 / blocked 13 / skipped 25 (Micron EXT timeout, Solera Workday login, Oracle OTP stale Gmail codes, Experian/JPMC CAPTCHA). Boards: 0. LinkedIn looping Micron persist_retry / Experian hCaptcha. No `/opt/cursor/artifacts/hitechcity-daily.json` written. Do not invent applies.

## Owner actions (not code-fixable)

1. **CAPTCHA / walls (Hitech):** Micron reCAPTCHA, Experian SmartRecruiters hCaptcha, JPMorgan bot wall; optional Solera Workday login; Accenture careers login (Naukri 3 walls).
2. **Approve/create PRs** — every portal agent pushed filter/API fixes but `gh pr create` failed (`Resource not accessible by integration` / ManagePullRequest awaiting approval). **No PRs opened or merged today.** Branches still on origin:
   - `cursor/linkedin-daily-2026-09-11-d286` (TITLE_OK / Boomi / AEC / filler)
   - `cursor/foundit-daily-2026-09-11-c8e0` (skip TAM / proposal SA / Atlassian ITSM)
   - `cursor/cutshort-daily-2026-09-11-7709` (Google SSO heal + terms checkbox)
   - `cursor/naukri-daily-2026-09-11-bbcf` (title skips / Wood / EM-AI)
   - `cursor/instahyre-daily-2026-09-11-bc9c` (candidate_matching apply API)
   - `cursor/indeed-daily-2026-09-11-355f` (Google SSO through cookie overlay)
   - `cursor/hirist-daily-2026-09-11-4994` (skip Workday/Teamcenter/AI-ML/Power BI)
   - `cursor/hitech-city-knowledge-city-daily-2026-09-11-5f26` (Agentic AI / Micron HW skips / OTP)
3. **`RESEND_FROM_EMAIL`** still unset (no verified Resend domain). This mail used `Job Status <onboarding@resend.dev>` and could only go to `rafi.success@gmail.com` (solibri.com rejected).
4. Google 2FA already cleared today for LinkedIn, Cutshort, Indeed, Hitech LinkedIn — no further phone prompts known.

## Fix PRs today (AUTO_FIX)

**Opened: 0. Merged: 0.** Same-day re-runs after merge did not happen (no merge). Portal agents could not open PRs with the integration token.

Stale open drafts from prior days remain (Cutshort daily reports, LinkedIn restriction guardrails, etc.) — none are today’s apply-fix PRs.

## Status-mail pipeline note

- Home-local DISABLED (no `fetch-home-result.sh`).
- Resend MCP used. `RESEND_FROM_EMAIL` unset; fallback `Job Status <onboarding@resend.dev>`. `RESEND_API_KEY` also unset in this pod.
- First send to `mohammed.ahmed@solibri.com` failed (Resend onboarding sender only allows `rafi.success@gmail.com` until a domain is verified). Delivered to `rafi.success@gmail.com` — id `e5f70fdf-86d6-40ca-b33c-9db1f737d891`.
- Counts are confirmed-submit only. Foundit redirects and LinkedIn/Naukri false-applies are called out, not hidden.
- Hitech City still RUNNING at send (0 confirmed applies). LinkedIn Easy Apply snapshot 15; agent later resumed — extra submits after 08:00 UTC are not in this mail.
