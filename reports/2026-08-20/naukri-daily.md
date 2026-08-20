# Naukri daily — 2026-08-20 IST (post-fix re-run after #220)

`POST_FIX_RERUN=1`. Started on merged `main` at PR [#220](https://github.com/rafi-solibri/MyRepo/pull/220) (shared `resume_paths`) + [#217](https://github.com/rafi-solibri/MyRepo/pull/217) (Mainframe/COBOL skip). Resume: `resumes/Rafi_Resume.docx`.

This is Naukri post-fix re-run **#2** today (cap 5). Earlier post-fix agent `bc-1fd3faaa` already applied after #217; this run executed the durable helper again and skipped jobs already submitted today.

PR [#222](https://github.com/rafi-solibri/MyRepo/pull/222) (per-job JD-tailored resume) merged while this worker was applying. This session’s 4 applies used the pre-#222 helper. Filter/CTA fixes below are rebased onto current `main` (includes #222). Sibling post-fix agents launched after #222 will apply with the tailor.

## STEP 0 — profile resume refresh

- **ok** — `profileUpdated: true`, `matchedToken: today`
- Resume shown: `Rafi_Resume.docx` / “Uploaded today”
- Headline touch: skipped (`headline_input_missing`)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## This session (after #220)

Counts: profileUpdated true / applied **4** / external **0** / blocked **1** / skipped **3150** / seen **223**

Ages: 1 → 3,7 → expand 15,30,60 + extra .NET/Azure queries.

### Applied (Naukri Quick Apply / chatbot, `Rafi_Resume.docx`)

1. **Kairos Technologies** — .Net Full Stack Architect/Application Technical Architect — Hybrid Hyderabad — Naukri — CTA `view_applied_jobs` — https://www.naukri.com/job-listings-net-full-stack-architect-application-technical-architect-kairos-technologies-hyderabad-10-to-20-years-200826013808
2. **Solugenix** — Software Architect — Hyderabad / Indore / Bengaluru — Naukri — CTA `chatbot:responses_thanks` — https://www.naukri.com/job-listings-software-architect-solugenix-indore-hyderabad-bengaluru-8-to-13-years-200826013705
3. **Globallogic** — C++ Media Lead Engineer I — Secunderabad / Pune / Bengaluru — Naukri — CTA `view_applied_jobs` — https://www.naukri.com/job-listings-c-media-lead-engineer-i-globallogic-pune-bengaluru-secunderabad-10-to-15-years-200826012458 — **false-apply: C++/media, not .NET; skip added**
4. **Ensemble Health Partners** — Lead Engineer, Software(dotnet) — Hybrid Hyderabad — Naukri — CTA `chatbot:responses_thanks` — https://www.naukri.com/job-listings-lead-engineer-software-dotnet-ensemble-health-partners-hyderabad-8-to-13-years-010626009206

External completed: **0**.

### Blocked

- **Accenture** — Packaged/SaaS App Engineering Lead — `external_incomplete_or_timeout` (MyCareer B2C login wall) — https://www.accenture.com/in-en/careers/jobdetails?id=ATCI-5698978-S2061194_en

### Already applied (not re-counted)

- Clean Harbors — .Net Fullstack Tech Lead (`already_applied_detail`)
- First American — Staff Software Engineer (`already_applied_detail`)

### Hirist login walls (skipped, not hard-blocked)

- Epam Systems — Full Stack Solution Architect Node.js/AngularJS
- Anlage Infotech — Blockchain/Digital Assets Engineering Lead
- Mancer Consulting Services — Engineering Manager - Platform
- Anlage Infotech — Full Stack AI Manager

Owner optional: Desktop Hirist login + re-seed session.

## Combined real applies today (do not double-count)

Morning (before #217): Epam Systems Solution Architect; Accordion Partners Technical Director.

First post-fix (after #217): Techstar Azure Senior DevOps Architect (**devops-primary false-apply; now skipped**). Morning also false-applied Netm Mainframe Architect (**now skipped by #217**).

This run: Kairos .NET Full Stack Architect; Solugenix Software Architect; Ensemble Health Partners Lead Engineer (dotnet). Globallogic C++ Media Lead is a **false-apply** (skip added).

## Code fixes this re-run

Cherry-picked from earlier agent (PR create was blocked there):

- `SKIP_TITLE_RE`: product manager, delivery partnerships, BRIM, OTC data migration/BRIM, devops architect, network architect
- `waitForVisibleApplyCta` + `handleExternal` retry company-site CTA

New this session:

- `NON_DOTNET_PRIMARY_RE`: skip `c++` / `c/c++` / `cpp` / `cplusplus` without .NET on the title (GlobalLogic C++ Media Lead)
- Tests: `node tools/naukri/test_filters.js` OK

## Artifacts

- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-daily-apply-postfix-2.json`
- `/workspace/artifacts/naukri-daily-apply.json`
