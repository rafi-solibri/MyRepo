# Job status — 2026-08-14

Job-status follow-up after daily force-all runner. Report run: https://cursor.com/agents/bc-0ca4be43-f083-40d3-a6a1-8b033c0f496e
Targets: Expected CTC 65 LPA; Hyderabad + Remote/WFH; resume `Rafi_Resume.docx`.
From: `Job Status <onboarding@resend.dev>` (`RESEND_FROM_EMAIL` unset — owner should set a verified sender secret).

**Do not invent applies.** Home-local same-day JSON missing for all portals (latest home: LinkedIn/Foundit/Cutshort 2026-08-11, Hitech 2026-08-12, Naukri/Instahyre/Indeed 2026-08-13). Cloud force-all post-fix re-runs were polled to IDLE before this mail.

Hotel Price Tracker (https://cursor.com/agents/bc-8764d5b0-4887-4c60-9e2a-4aa457a644ce) is **not** a job-apply automation — left to its own email.

## Combined confirmed applies (cloud, 2026-08-14)

**This force-all wave: 34** (LinkedIn 10 + Foundit 2 + Cutshort 1 + Naukri 14 + Instahyre 0 + Indeed 6 + Hitech 1).

**Earlier same-day cloud (before force-all), not re-counted in the 34:** Foundit +4 (410→414, includes 1 false Agentforce); Naukri morning 8 + #142 re-run 4 + ensure-missing 2; Instahyre ensure-missing 2; Hitech morning agent still RUNNING at 04:37 UTC with 1 partial Naukri board apply.

| Portal | Source | Applied | External | Rejected | Blocked | Skipped | Seen | Status | Blocker |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| LinkedIn | cloud force-all | 10 | 0 | — | 5 | 107 | 122 | IDLE | CAPTCHA/checkpoint after helper crash; inventory unfinished |
| Foundit | cloud force-all | 2 | 0 confirmed | — | 0 | 498 | — | IDLE | none (1 false sales apply) |
| Cutshort | cloud force-all | 1 | 0 | 0 | 0 | 0* | 1187 | IDLE | none (*filter skips not in counts.skipped) |
| Naukri | cloud force-all | 14 | 0 | — | 34 then 2 | 2680 then 471 | 276 then 69 | IDLE | Workday ATS walls; 0 company-site completes |
| Instahyre | cloud force-all | 0 | — | — | 0 | 678 | 678 | IDLE | inventory exhausted (already interested / location) |
| Indeed | cloud force-all | 6 | 21 opened (not submitted) | 10 | 16 | 48 | 101 | IDLE | Easy Apply reCAPTCHA (16); CF cleared |
| Hitech City | cloud force-all | 1 | 0 | — | 64 | 3632 | 3697 | IDLE | LinkedIn CAPTCHA after boards; careers CAPTCHA/Amazon; Indeed board login_required |
| LinkedIn home | home-local | — | — | — | — | — | — | missing | **linkedin home result missing** for 2026-08-14 |
| Foundit home | home-local | — | — | — | — | — | — | missing | **foundit home result missing** for 2026-08-14 |
| Cutshort home | home-local | — | — | — | — | — | — | missing | **cutshort home result missing** for 2026-08-14 |
| Naukri home | home-local | — | — | — | — | — | — | missing | **naukri home result missing** for 2026-08-14 |
| Instahyre home | home-local | — | — | — | — | — | — | missing | **instahyre home result missing** for 2026-08-14 |
| Indeed home | home-local | — | — | — | — | — | — | missing | **Indeed home result missing** for 2026-08-14 (latest 2026-08-13 Cloudflare private-worker) |
| Hitech home | home-local | — | — | — | — | — | — | missing | **hitechcity home result missing** for 2026-08-14 |

## 1) LinkedIn Daily 9 AM

- Automation: https://cursor.com/automations/beb6ef8e-908f-11f1-ba66-0e7d0216e441
- Force-all agent: https://cursor.com/agents/bc-b73ef711-4905-4310-af7f-19e7548cf4d6 (**IDLE**)
- Home: **linkedin home result missing** for 2026-08-14 (latest home 2026-08-11)
- Cloud: applied **10** Easy Apply (`Application submitted`), external **0** (not attempted after checkpoint), blocked **5**, skipped **107**, seen **122**
- Login: password auto-login OK at start; helper crashed (`Page.reload` / detached frame); resume hit **`captcha_checkpoint`** (AUTO_RC=6)
- Confirmed Easy Applies (helper stored title in company field): 8× Solutions Architect - Microsoft Fabric; Engineering Manager; Interior Architect (agent labeled false-apply BArch); Snowflake Solutions Architect Kerala (agent labeled false-apply)
- Owner: headed login + complete LinkedIn security checkpoint + Save snapshot. External ATS pass not run.

## 2) Foundit Daily 9 AM

- Automation: https://cursor.com/automations/5d1b07b2-90a9-11f1-ba66-0e7d0216e441
- Force-all agent: https://cursor.com/agents/bc-f8ae2bb0-c8f7-4f3c-953a-77338783bc71 (**IDLE**)
- Home: **foundit home result missing** for 2026-08-14
- Cloud this wave: applied **2** (Applied tab 415→417), blocked **0**, skipped **498**, duplicates **38**. Login OK (`Hi Rafi`).
- Applied: Sprinto Senior Staff Engineer (India remote, Falcon + LinkedIn no Easy Apply); Deltek Accounts Manager / Principal Sales Rep (false apply — `principal` rode #151 Arch/Lead bypass)
- Earlier today: 410→414 (+4) including Salesforce Agentforce false apply (fixed in #140; post-#140 re-run +0)
- Filter fix pushed on `cursor/foundit-fix-skip-sales-principal-a239` — **PR not opened** (`gh` 403)

## 3) Cutshort Daily 9 AM

- Automation: https://cursor.com/automations/d6ba8b9d-9094-11f1-ba66-0e7d0216e441
- Force-all agent: https://cursor.com/agents/bc-02774d51-5a87-4d18-bb92-c3fdeaf563b2 (**IDLE**)
- Home: **cutshort home result missing** for 2026-08-14
- Cloud: applied **1**, external **0**, rejected **0**, blocked **0**, seen **1187**, qualifying **1**. Login OK (earlier same-day stub was login-wall).
- Applied: Orangemint Technologies — Senior Technical Consultant — remote — `api_no_ui_button`
- Notes: `q_locked_empty=322` (historical API-locked, not same-day apply failures)

## 4) Naukri Daily 9 AM

- Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
- Force-all agent: https://cursor.com/agents/bc-a5ece630-45d4-4747-a5cf-e187252c7dc2 (**IDLE**)
- Home: **naukri home result missing** for 2026-08-14
- Cloud this wave: pass 1 applied **12** / blocked **34** / skipped **2680** / seen **276**; pass 2 applied **2** / blocked **2** / skipped **471** / seen **69**. Session applied **14**. External completed **0**. Profile resume refreshed today.
- Login OK. Attack Surface Reduction was **not** re-applied (#149 on main).
- Pass 1 applied: Movate Data Solution Architect; PwC Azure/AWS Architect-Manager; TCS Azure AI ML Architect; Clean Harbors Architect - Mobile Applications; Luxury Screens Marketing Director (filter miss); Tredence Dot Net Architect; Hexaware Data Platform Solution Architect; MANEVA Oracle C2M Solution Architect (filter miss); SHI Senior Solution Architect Network & Security; JIRA Atlassian Architect; Leading Consumer Products GCC Endpoint Architect; Trackmind Pricing Architect
- Pass 2 applied: Naukri Assist Azure Cloud Solution Architect; TCS TOSCA Automation Architect (filter miss)
- Earlier today (separate agents): morning 8 + #142 re-run 4 + ensure-missing 2 (Nopal Attack Surface — false apply later skipped by #149; Big 4 Dotnet Full stack with AI Manager)
- Filter tightening pushed on `cursor/naukri-daily-post-fix-re-run-2026-08-14-67c0` — **PR not opened** (`gh` 403)
- Workday/Medtronic ATS login walls remain owner-capped, not Naukri login failure

## 5) Instahyre Daily 9 AM

- Automation: https://cursor.com/automations/1d0ea682-9093-11f1-ba66-0e7d0216e441
- Force-all agent: https://cursor.com/agents/bc-8a58a309-e284-4a81-ab2c-1c44649c1d45 (**IDLE**)
- Home: **instahyre home result missing** for 2026-08-14
- Cloud this wave: applied **0**, blocked **0**, skipped **678**, seen **678**. Login OK. Interested stayed **449**.
- Top skips: location_not_hyd_remote 553; already_interested 90
- Earlier today (ensure-missing, not this wave): Divisions Maintenance Group Engineering Manager; Ansrsource Lead Software Engineer

## 6) Indeed (home-local preferred; cloud used because same-day home JSON missing)

- Automation: https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441
- Force-all agent: https://cursor.com/agents/bc-1cbd1811-1691-43ee-a244-8fd89c5d8ceb (**IDLE**)
- Home: **Indeed home result missing** for 2026-08-14 (latest home 2026-08-13: applied 0 / blocked 1 / `indeed_cloudflare_private_worker_required`)
- Cloud: CF preflight **ok** (WARP+UC). First two apply passes `indeed_login_required`; after cookie-decrypt + JWT refresh, third pass applied **6** Easy Apply. Final counts: applied **6**, external **21** (company site opened, not confirmed submits), rejected **10**, blocked **16** (Easy Apply reCAPTCHA), skipped **48**, seen **101**. `blockerSummary: easy_apply_recaptcha` with `ok: true`.
- Applied: Technology Next Kafka Architect (Hyd); UHV Sr. Monitoring Architect (Hyd); InvoiceCloud .Net/C# Developer PRE (Hyd); Jinendra DOT NET TECH LEAD (Hyd); CACI Senior Site Reliability Engineer (Hyd); Impelsys .Net Lead/Senior Software Engineer (Bangalore / LATAM Remote — location-filter leak, still submitted)
- Cookie-decrypt fix pushed on `cursor/indeed-fix-uc-cookie-decrypt-a239` — **PR not opened** (`gh` 403)

## 7) Hitech City / Knowledge City Daily

- Automation: https://cursor.com/automations/b65968f7-953d-11f1-ba66-0e7d0216e441
- Force-all agent: https://cursor.com/agents/bc-8016b6dc-3dd4-4740-b299-e77aa6bbb667 (**IDLE**)
- Artifact: `/opt/cursor/artifacts/hitechcity-daily.json` present in that agent (not this mail-job pod)
- Home: **hitechcity home result missing** for 2026-08-14
- Cloud totals: applied **1**, external **0**, blocked **64**, skipped **3632**, seen **3697**, referralsSent **0**
  - LinkedIn: applied 0 / blocked 30 / skipped 157
  - Careers: applied 0 / blocked 32 / skipped 20
  - Boards: applied 1 (Naukri) / Foundit 0 / Cutshort 0 / Instahyre 0 / Indeed error `indeed_login_required`
- Applied: Software Product / Sangathr Career Management Consultants — AI Full stack Application Architect — Naukri recommended chatbot (off-campus allowlist miss; listing Chennai)
- Owner: LinkedIn CAPTCHA after boards; Amazon passport / career CAPTCHA; Indeed headed login for board path
- Fixes pushed on `cursor/hitech-city-knowledge-city-daily-post-fix-re-run-2026-08-14-6a6f` — **PR not opened** (`gh` 403)
- Morning agent https://cursor.com/agents/bc-09f94d65-caa2-4256-aac6-e64466c28b81 was still RUNNING at the 04:37 UTC mail (partial 1 Naukri board apply)

## Today's fix PRs (merged on main before/during 2026-08-14)

- #151 feat(automation): implement max-apply volume recommendations
- #149 fix(naukri): skip attack-surface / cybersecurity primary titles
- #148 fix(automation): do not force-restore portal seeds over live CDP auth
- #147 fix(automation): re-run failed/missing dailies; raise Cutshort India/.NET volume
- #146 docs: 2026-08-14 missing-portal recovery reports + auto-merge PR URL fix
- #145 fix(cutshort,instahyre,indeed): survive CDP close; detect Indeed anon session
- #144 fix(automation): stop parallel issue-log collisions; recover missing dailies
- #143 fix(hitechcity): harvest board applies on timeout; skip Salesforce Service Cloud
- #142 fix(naukri): recover chatbot Save + expand bad-title skips
- #141 docs(foundit): record 2026-08-14 post-fix re-run results
- #140 fix(foundit): skip Agentforce/SFDC and Salesforce-employer non-.NET titles

Open: #150 HitechCity coverage detection + reports; #134 2026-08-13 docs; #93 2026-08-12 docs.

Force-all agents could not open PRs (`Resource not accessible by integration`). Unmerged branches: Foundit sales-principal skip; Naukri director/architect filter; Indeed UC cookie decrypt; LinkedIn reload/CAPTCHA helpers; Hitech LinkedIn-tab recover + Naukri allowlist.

## Owner actions (not code-fixable)

1. LinkedIn headed checkpoint: `bash scripts/home-headed-login.sh linkedin` then Save snapshot (CAPTCHA after 10 Easy Applies).
2. Indeed home/residential path still preferred; cloud applied 6 after in-session cookie decrypt, but 16 Easy Apply reCAPTCHAs remain.
3. Hitech careers: Amazon passport + CAPTCHA (Experian/Palo Alto-class walls).
4. Set secret `RESEND_FROM_EMAIL` to a verified domain sender (mail used onboarding fallback).
5. Approve/open the force-all agent branches (gh 403 in those pods).
6. Evening home-local Task Scheduler runs still expected; same-day home JSON was missing for every portal.

## Mail pipeline note

Resend MCP: connected. Email sent via Resend MCP — id `39fec0b9-02ff-40bc-8e7d-456ebd060158`.
`scripts/fetch-home-result.sh <portal> --today` ran for all seven portals; all `sameDay: false` → reported as home result missing (no invented applies).
No mail-pipeline code fix this run.
