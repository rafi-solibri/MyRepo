# Naukri daily — 2026-08-22 (post-fix re-run on merged #235)

Same-day re-run after [PR #235](https://github.com/rafi-solibri/MyRepo/pull/235) (`4d6c615` on `main`). `POST_FIX_RERUN=1`. Agent: https://cursor.com/agents/bc-dc0dcb0b-6d42-420f-bc9f-69560d368c66

This session ran `daily_apply.js` **with the merged skip filters**. It does **not** re-count the morning cron’s 6 applies (those ran on pre-fix code).

## 1) Profile resume refresh
- **ok** — `profileUpdated: true`
- Resume filename shown: **Rafi_Resume.docx**
- Signal: `Uploaded today` / matched token `today`
- Upload via `input[id*='resume' i][type='file']` + Update
- Canonical CV restored at end of run (`profileResumeRestored.ok: true`)

## 2) Applies this session
**None confirmed.** Do not invent applies. Eligible Naukri Quick Apply inventory was already consumed by the morning cron (and a sibling post-fix agent also recorded 0 new applies).

### Already applied earlier today (not re-counted)
- Clean Harbors — .Net Fullstack Tech Lead (Naukri CTA `Applied`)
- First American — Staff Software Engineer (homepage CTA `Applied`)

Morning cron (pre-#235, not this session): TCS Enterprise Infra & Cloud Architect; TCS Solution Architect; Insight Global Solution Architect; plus three false-applies that #235 now skips (MS Fabric/Synapse/Databricks staffing; Sonata DevOps Architect; Mulesoft Architect).

### Hirist login walls (skipped, not hard-blocked)
- BLJ Tech Geeks — Senior Manager/GCC Account Lead - Solution Architecture (12-20 yrs) — tailored `Rafi_Resume.docx`
- Epam Systems — Full Stack Solution Architect - Node.js/AngularJS (10-20 yrs) — tailored `Rafi_Resume.docx`
- Anlage Infotech — Full Stack AI Manager (10-13 yrs) — tailored `Rafi_Resume.docx`
- Mancer Consulting Services — Engineering Manager - Platform (10-15 yrs) — tailored `Rafi_Resume.docx`

### CTC / location skips of note
- Incedo — .Net Lead role- Immediate joiner — `skip_ctc_max_30` (listed max &lt; 35 LPA)
- First American / Fiserv / Mastercard EM-or-Principal cards — non-Hyd / non-remote (`skip_location`)

## Counts (this session)
`profileUpdated: true` / **applied: 0** / **externalCompleted: 0** / **blocked: 0** / **skipped: 2909** / **seen: 202** / tailoredApplies: 0

Skip mix: 2687 `duplicate_in_run` · 135 `skip_title_keyword` (incl. #235 Mulesoft/Fabric/DevOps/AI/Java) · 37 `skip_no_dotnet` · 28 `skip_seniority` · 7 `skip_location` · 4 `skip_company` · 4 Hirist · 5 CTC-under-35 · 2 already applied.

Search expanded 1→3/7 then 15/30/60 plus extra .NET/Azure queries; recommended + homepage pass included.

## Artifacts
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-daily-apply-run.log`

## Auto-fix
No **new** apply-unlocking code fix in this session. PR #235 is already on `main`. Post-fix re-runs today: this agent + sibling `bc-5b2bbc4e` (also 0 new applies). Cap 2/5 — no further re-run launched.

Owner-only residual: optional Hirist login + re-seed (walls skipped per prompt).
