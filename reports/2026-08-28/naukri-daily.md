# Naukri daily — 2026-08-28 (post-fix re-run after #280)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
This run: https://cursor.com/agents/bc-1bd1d183-5302-4260-a396-44be5e184a4a
Earlier morning run (applied without #280): https://cursor.com/agents/bc-f476e01f-b101-4a14-bad0-5cfeb06aec1b
Merged fix used: https://github.com/rafi-solibri/MyRepo/pull/280 @ `93e35d6`

`POST_FIX_RERUN=1`. First Naukri same-day re-run (cap 5).

## Profile resume refresh (STEP 0)
- **ok** — `profileUpdated: true`
- Resume: `resumes/Rafi_Resume.docx` (rebuilt from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx`, 20945B)
- Verify: **Uploaded today**
- Canonical CV restored at end of run: **ok**

Login: live CDP `nauk_rt`/`nauk_at` + homepage OK (`wait_for_cdp_login.js`).

## Helper counts
- Applied (helper-confirmed): **0**
- External / company-ATS completed: **0**
- Blocked: **1** · Skipped: **3087** (2851 duplicates) · Seen unique: **213**
- Ages: 1 → early-expand 3,7 → expand 15,30,60 + extra .NET/Azure queries

## Verified apply (not invented)
Helper logged Recruise as `apply_unconfirmed` (empty CTA, `no_chat`). After the run, the job-listings page showed a **disabled** dual-layer `Quick apply Applied` button — Naukri's landed-apply signal.

| Company | Role | Path | Resume | Notes |
| --- | --- | --- | --- | --- |
| Software Company / Recruise India Consulting | Engineering Manager | Naukri Quick Apply | tailored `Rafi_Resume.docx` | Helper unconfirmed; live CTA disabled Applied |

## Already applied (skipped, not re-counted)
- Clean Harbors — .Net Fullstack Tech Lead (`already_applied_detail`, CTA Applied)

## Blocked / walls
- Recruise EM — helper `apply_unconfirmed` (see verified apply above)
- Highradius TechOps, Anlage AI Platform, Rapidue SA — `hirist_login_required_skip` (not hard-blocked)
- Incedo — .Net Lead Immediate joiner — `skip_ctc_max_30` (listed max 30 < 35)

#280 Workday phone/company fill was not exercised — no eligible Workday/company-site jobs in this inventory.

## Inventory note
Eligible Hyd/remote .NET Arch/Lead/EM inventory was thin. Remaining .NET titles were developer seniority (Mouri/LTM/Assurant/Ascentforce) or already applied (Clean Harbors). Arch/EM cards were mostly Java/Salesforce/Python/AI and correctly title- or JD-skipped.

## New code-fixable blockers this re-run
1. **Empty-CTA confirmation miss:** Recruise apply landed (disabled dual-layer) but `confirmApplied` returned `apply_unconfirmed` because the overlay/list tab had no readable CTA. Fix: reload `job-listings` URL and re-read disabled/Applied.
2. **Architecting false skip:** GERENT “Solution Architecting, Solution Design, Delivery Leadership” hit `skip_no_dotnet` because `ARCH_LEAD_RE` matched `architect(ure)?` but not `architecting`.

Do not invent further applies. Same-day re-run after this fix should skip Recruise as already applied and retry GERENT via the Arch/Lead exemption + JD filter.
