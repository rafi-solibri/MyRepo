# Job status — 2026-08-15  <!-- pragma: allowlist secret -->

Manual full daily status-mail job after morning cron + earlier post-fix re-runs did not produce usable same-day coverage.
Report run: https://cursor.com/agents/bc-2d8f7154-5538-4b18-ac97-8eb8bfe89b57
Waited for named apply agents (LinkedIn / Foundit / Cutshort / Naukri / Instahyre / Indeed / Hitech City Daily 2026-08-15) until IDLE (~75 min).  <!-- pragma: allowlist secret -->
Targets: Expected CTC 65 LPA; Hyderabad + Remote/WFH; resume `Rafi_Resume.docx`.
`FORCE_RESTORE_SESSIONS` was not set.
From note: `RESEND_FROM_EMAIL` unset — sent via `Job Status <onboarding@resend.dev>`.

## Summary

Home-local same-day JSON **missing** for all portals (`fetch-home-result.sh <portal> --today` and `fetch-indeed-home-result.sh --today`). Latest home dates: LinkedIn/Foundit/Cutshort 2026-08-11; Naukri/Instahyre 2026-08-13; Indeed 2026-08-14 Cloudflare blocked; Hitech City 2026-08-12. **Did not invent applies from stale home JSON.**

Preferred source: same-day cloud artifacts from the named Daily 2026-08-15 agents (all IDLE).  <!-- pragma: allowlist secret -->

**This wave (named 7) new applies: 59** — Foundit 39 + Cutshort 3 + Naukri 3 + Indeed 8 + Hitech City Foundit boards 6.
**Earlier same-day (morning / first post-fix, already emailed 10:11 IST):** Foundit 4 + Naukri 1 (Xanika) + Indeed 5 = 10.
**Combined known distinct applies today: 69.** Later #160/#161/#162 post-fix waves were still RUNNING at send time — not counted.

## Portal table (this wave — named Daily 2026-08-15)  <!-- pragma: allowlist secret -->

| Portal | Applied | External | Rejected | Blocked | Skipped | Seen | Home | Blocker / notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| LinkedIn | 0 | 0 | — | 1 | 0 | 0 | missing | CAPTCHA / `/checkpoint/challenge` after Google SSO |
| Foundit | 39 | 25 LI no EA; 5 incomplete; 2 login | 0 | 0 | 1328 | — | missing | Extra Arch/Lead wave after .NET queries exhausted; 413→451 |
| Cutshort | 3 | 0 | 0 | 0 | 0 | 3197 | missing | pageSize/expMax fix in-session; 322 historical locked-empty |
| Naukri | 3 | 0 | 0 | 1 | 3426 | 206 | missing | Chatbot multiselect + military chips; Lloyds Workday maintenance |
| Instahyre | 0 | 0 | 0 | 0 | 678 | 678* | missing | Hyd/WFH pool exhausted (`already_interested` 88); *uniqueJobsSeen |
| Indeed home | 0* | 0* | 0* | 1* | 0* | 0* | **missing** | *stale 2026-08-14 `indeed_cloudflare_private_worker_required` |
| Indeed cloud | 8 unique | 24 | 11 | 7 | 44 | 90 | n/a | Pass 2 artifact; mostly `easy_apply_recaptcha` |
| Hitech City | 6 | 0 | — | 9 | 3369 | 3378 | missing | Careers 0; LinkedIn CAPTCHA; Foundit boards 451→457 |

## 1) LinkedIn Daily 2026-08-15  <!-- pragma: allowlist secret -->

- Agent: https://cursor.com/agents/bc-45718255-5a39-4862-a3c0-a78f1025e911 — IDLE
- Home: linkedin home result missing (latest 2026-08-11)
- Applied 0 / external 0 / skipped 0 / blocked 1 / seen 0
- blockerSummary: LinkedIn Security Verification (reCAPTCHA) after Continue with Google; live `li_at` absent; helpers not started
- Morning + earlier post-fix also 0 (CAPTCHA). #157 already merged; this run did not open a new PR (owner-only)
- Owner: `bash scripts/home-headed-login.sh linkedin` then refresh session seed + Save snapshot

## 2) Foundit Daily 2026-08-15  <!-- pragma: allowlist secret -->

- Agent: https://cursor.com/agents/bc-739d350c-0a74-4d73-aa9d-f925008f5908 — IDLE
- Home: foundit home result missing (latest 2026-08-11)
- First pass: 405→405, 0 new (primary .NET queries exhausted)
- Final: applied **39** / skipped 1328 / blocked 0; dashboard 413→451 (delta 38; 39 intentional Falcon)
- 9 native Foundit (`NORMAL`); 30 redirect-stage; external ATS: 25 LinkedIn no Easy Apply, 5 incomplete/cap, 2 login walls
- Titles include: Jobgether Principal SA; Jobgether HubSpot/Clio SA; Zensar Wealth Management SA; TTEC Solutions Architect-IP; Uplers Technical Architect; AST SpaceMobile Partner Technical Lead; Flexiple Product EM; L&T Engineering Manager; Egnyte Principal Engineer - AI; Microsoft Principal Firmware Verification; Accenture Cloud Platform Architect; Deloitte Applied AI Platform (BOOMI / PEGA); PepsiCo Deputy Director SWE; Infosys / TCS / Delphi Cloud Architect; Sonata D365 Technical Architect; Hitachi Energy EM; Uber Sr Staff SWE; Everstage Senior Technical Software Architect; Aprimo Technical Solution Architect; Avalara Principal SWE/Architect-AI; Centroid OCI Cloud Architect; Vertafore DB cloud Performance Architect; plus others in the 39
- Fix branch pushed (`cursor/foundit-daily-2026-08-15-0853`); **PR not created** (`gh` read-only)  <!-- pragma: allowlist secret -->
- Morning cron had applied 4 earlier (relq; Closeloop EM; Kumaran Lead .Net; infomatix Senior .NET) — already in 405 baseline, not in the 39

## 3) Cutshort Daily 2026-08-15  <!-- pragma: allowlist secret -->

- Agent: https://cursor.com/agents/bc-7adda525-5116-4e0f-b1b6-400d291b5b9b — IDLE
- Home: cutshort home result missing
- Pass 1: seen 1179 / qualifying 0 / applied 0 (pageSize=5 + expMax filter)
- Pass 2 (authoritative): applied **3** / external 0 / rejected 0 / blocked 0 / skipped 0 / seen 3197; q answered 2; locked-empty 322 (historical)
- Applied: Principal Engineer, Salesforce Health Cloud @ Unique Occupational; Senior Full-Stack Engineer @ Recro; Sr. AI Ops Engineer @ Fx31labs
- Fix branch `cursor/cutshort-fix-pagesize-exp-a239` pushed; **PR not created** (403)

## 4) Naukri Daily 2026-08-15  <!-- pragma: allowlist secret -->

- Agent: https://cursor.com/agents/bc-007240b7-1e18-4135-8bbf-60b74809b580 — IDLE
- Home: naukri home result missing (latest 2026-08-13 applied 21 — not today)
- Morning cron agent: none; earlier post-fix applied 1 (Xanika Infotech — PROS CPQ Solution Architect) — skipped as already applied this wave
- This wave confirmed **3** Quick Applies: Jade Global Lead AI Engineer; LRR Technologies Senior Lead Engineer For Top MNC; PwC Technical Lead - Manager
- Final pass artifact: applied 2 / external 0 / blocked 1 / skipped 3426 / seen 206 (Jade counted on prior in-session re-run)
- Blocked: Lloyds Technology Centre Engineering Lead — Workday maintenance (`external_incomplete_or_timeout`)
- Fix branch `cursor/naukri-fix-chatbot-multiselect-a239` pushed; **PR not created**

## 5) Instahyre Daily 2026-08-15  <!-- pragma: allowlist secret -->

- Agent: https://cursor.com/agents/bc-f0832b22-194b-47da-a2aa-95633046e5c3 — IDLE
- Home: instahyre home result missing (latest 2026-08-13)
- Applied 0 / external 0 / rejected 0 / blocked 0 / skipped 678 / uniqueJobsSeen 678
- blockerSummary: null — inventory exhaustion, not a login failure. Interested 449→449. 88 already_interested; 553 location_not_hyd_remote
- Same result as morning cron. No fix PR

## 6) Indeed

- Home: `bash scripts/fetch-indeed-home-result.sh --today` → **Indeed home result missing** (sameDay false; date 2026-08-14; applied 0 / blocked 1; `indeed_cloudflare_private_worker_required`). Not used as today’s Indeed.
- This wave: https://cursor.com/agents/bc-1132d20d-d071-43cf-b790-e852cc735413 — IDLE
- **8 unique Easy Apply** (pass 1 applied 4; pass 2 artifact applied 5 / external 24 / rejected 11 / blocked 7 / skipped 44 / seen 90)
- Applied: Ampleopp Dynamics 365 CRM Senior Developer; Centroid OCI Cloud Architect C2H; Recruise AWS Solution Architect; QualMinds Software Engineer C#.NET; Two95 .Net Developer with PLANISWARE; Cidroy Senior Solution Architect (Remote); Nagarro Senior Staff Engineer .Net Fullstack (Remote); Nagarro Senior Engineer .Net Web (Remote)
- blockerSummary: None (session warmed via Passport). Per-job `easy_apply_recaptcha` remains
- Fix commits on `cursor/indeed-daily-2026-08-15-f01b`; **PR not created**  <!-- pragma: allowlist secret -->
- Earlier same-day (morning post-fix #158, already emailed): applied 5 — Quest Global HMI; Celersoft senior systems architect; Softomatic Oracle EPM SA; Anblicks Snowflake Architect; VT NETZWELT Principal AI Architect

## 7) Hitech City / Knowledge City Daily 2026-08-15  <!-- pragma: allowlist secret -->

- Agent: https://cursor.com/agents/bc-6b6108f6-1d1d-4dc4-8efd-95e4d9383bdb — IDLE
- Home: hitechcity home result missing (latest 2026-08-12)
- First pass: applied 0 / blocked 9 / skipped 3369 / seen 3378 (careers 0/6/12; LinkedIn CAPTCHA; boards 0)
- After Foundit-only in-session re-run: applied **6** (Foundit Falcon; profile 451→457). Careers 0; LinkedIn referrals 0
- Applied: Virtusa .NET Tech Lead; Infosys .Net Core Lead (Hyd); Capgemini .Net Azure/AWS Lead (ATS incomplete); Microsoft Principal Technology Consultant Apps Full stack ×3 (ATS 404 / no Easy Apply)
- LinkedIn discovery blocked (CAPTCHA). Careers: Experian CAPTCHA; Microsoft/Qualcomm/Solera login walls
- Fix branch `cursor/hitechcity-fix-board-india-exp-a239` pushed; **PR not created**

## Today’s fix PRs

**Merged:**
- https://github.com/rafi-solibri/MyRepo/pull/157 — fix(linkedin): welcome-back Google SSO
- https://github.com/rafi-solibri/MyRepo/pull/158 — fix(indeed): reload after Turnstile
- https://github.com/rafi-solibri/MyRepo/pull/159 — fix(hitechcity): Architecture titles + prune junk tenants
- https://github.com/rafi-solibri/MyRepo/pull/160 — fix(ats): complete company-website applies
- https://github.com/rafi-solibri/MyRepo/pull/161 — fix(ats): max company-site applies
- https://github.com/rafi-solibri/MyRepo/pull/162 — fix(ats): submit company-site applies instead of timing out on hops

**Pushed this wave, PR create failed (owner must open/merge):**
- Foundit extra Arch/Lead query + non-India location fix
- Cutshort pageSize=50 + senior expMax
- Naukri chatbot multiselect + military-service chips
- Indeed Passport warm + SmartApply form fills
- Hitech City board India-only + Lead 6–9

Open drafts (not today’s apply fixes): #153, #150, #134, #93.

#160/#161/#162 launched additional post-fix re-runs after the named 7 finished; those were still RUNNING at send time and are **not** included in the 59/69 totals.

## Owner actions (not code-fixable)

1. LinkedIn headed CAPTCHA: `bash scripts/home-headed-login.sh linkedin` → refresh `.portal-sessions` → Save snapshot
2. Indeed home-local: private worker / residential path (`indeed_cloudflare_private_worker_required` on 2026-08-14 home JSON)
3. Hitech City career SSO/CAPTCHA walls (Microsoft / Qualcomm / Solera / Experian)
4. Set `RESEND_FROM_EMAIL` to a verified sender (still using `onboarding@resend.dev`)
5. Naukri morning cron enabled but produced no morning agent today
6. Approve/create the unmerged portal fix PRs from this wave (Cutshort pageSize, Naukri chatbot, Foundit extra queries, Indeed SmartApply, Hitech board filters)

## Mail pipeline

- Resend MCP: ready — email id `91151fe6-2d04-461e-a7b7-a2ba63c1d2af` (usual status recipient)
- Home fetches: all seven + Indeed helper ran; none same-day
- No mail-pipeline code fix this run
