# Naukri daily — 2026-08-19 (post-fix re-run #2, merged main)

Re-run of [Naukri Daily 9 AM](https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441) after merged PR [#214](https://github.com/rafi-solibri/MyRepo/pull/214).
Agent: https://cursor.com/agents/bc-644010dd-59f2-4d8e-aca5-f2e4a4d0869f
Code: `231b56e` on `main` (pulled before applies). `POST_FIX_RERUN=1`. Cap 2/5 same-day Naukri re-runs.

## 1) Profile resume refresh
- **ok** — `profileUpdated: true`, `todayHit: true`, matched token `today`
- UI: `Rafi_Resume.docx` / **Uploaded today** (`updateOn` empty)
- Upload via `input[id*='resume' i][type='file']` + Update button
- Headline touch skipped (`headline_input_missing`)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## 2) Confirmed applies (do not invent others)

| Company | Role | Location | Path | Job URL | Resume |
|---|---|---|---|---|---|
| Healthedge | Technical Lead | Hybrid - Hyderabad | Naukri chatbot (`responses_thanks`) | https://www.naukri.com/job-listings-technical-lead-healthedge-hyderabad-11-to-15-years-190826013498 | Rafi_Resume.docx |
| Jconnect Infotech *(card: “Hiring for a Miscellaneous company”)* | AWS Architect | Hyderabad, Noida, Gurugram | Naukri chatbot (`responses_thanks`) | https://www.naukri.com/job-listings-aws-architect-jconnect-infotech-noida-hyderabad-gurugram-9-to-20-years-190826016578 | Rafi_Resume.docx |

## Counts
profileUpdated **1** / applied **2** / external **0** / blocked **3** / skipped **2821** / seen **228**
Early-expand ages 3,7 (applied=2&lt;3); expand 15/30/60; extra .NET/Azure queries. 288 query runs.

## Blocked (not confirmed applies)
- **PwC** — Solution Architect Senior Manager — Hyd/Bengaluru — `apply_unconfirmed` / `chat_steps_exhausted` — https://www.naukri.com/job-listings-solution-architect-senior-manager-pwc-hyderabad-bengaluru-10-to-20-years-190826016782
- **Dtcc** — Lead Software Engineer — Hyderabad — Oracle Cloud HCM `external_incomplete_or_timeout` — https://ebxr.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/213622/easy-apply/email
- **Principal Financial Group** — Associate Director - Engineering — Hyderabad — `chat_steps_exhausted` (recurring) — https://www.naukri.com/job-listings-associate-director-engineering-principal-financial-group-hyderabad-18-to-23-years-050826031938

## Already applied (skipped, not re-counted)
- i2e Consulting — Solution Architect — `130826013685` (CTA Applied)
- Clean Harbors — .Net Fullstack Tech Lead — `230226023126` (CTA Applied)

Today’s earlier Naukri runs also submitted Lecan, Solugenix (two listings), Agilisium, Intrics — those did not re-appear as apply CTAs here.

## Other skips (not hard-blocked)
- 6× Hirist login wall (`hirist_login_required_skip`): ValGenesis, First American ×2, Anlage Infotech, Rapidue, Mancer
- Incedo `.Net Lead` skipped `skip_ctc_max_30` (listed max 30 &lt; 35 threshold — correct)
- Salesforce/Pega/etc. via `skip_company`; cyber/QA/GenAI via `skip_title_keyword`

## New code-fixable blocker this re-run?
None launched. Chatbot `chat_steps_exhausted` (PwC / Principal Financial) is a recurring wall, not a durable helper bug. DTCC Oracle Cloud timed out inside the 6.5m ATS budget. Earlier unmerged Naukri filter/Workday patches (Power BI / MuleSoft / EDI / View-applied / Workday India phone) did not fire on this inventory and were **not** cherry-picked (would force another re-run).

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-daily-apply.log`
- `/opt/cursor/artifacts/portal-login-status.json`
