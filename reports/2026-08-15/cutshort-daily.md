# Cutshort daily 2026-08-15 (post-fix re-run, #164) <!-- pragma: allowlist secret -->

**POST_FIX_RERUN=1** on merged `main` @ `586c376` (`fix(ats): fail-fast brochure pages and false Apply CTAs so external applies complete` #164).

This is same-day post-fix re-run **5 of 5** (cap). Earlier original daily and prior re-runs did **not** apply with #164. This session pulled `main`, ran `bash scripts/preflight-portal-run.sh` + Chrome CDP (synced portal profile), verified `tools/.../questionnaire.js`, and executed `node tools/.../daily_apply.js` with `Rafi_Resume.docx`.

Login: OK (candidate dashboard, live CDP, portal auth cookie present). Resume: `/workspace/resumes/Rafi_Resume.docx`. Runner EXIT=0 (07:40–07:52 UTC).

## Counts (this pass — not invented)
- Scanned: **3198** (`pageSize=50`; newest total_count=3217)
- Qualifying: **0**
- Applied: **0**
- Already (this pass): 0
- Failed/blocked (apply): 0
- External: 0 (no qualifying company-site cards — #164 brochure/false-CTA path unused)
- Q answered: **0** | already-submitted: 41 | locked-empty: **322** (historical API locks, not same-day apply failures) | verify-empty: 0
- Awaiting listed: 367
- Failures (apply + locked-empty + verify-empty): **322**
- Same-day apply failures: **0**

Skip taxonomy: `location=213` `skip_title=757` `ctc_under_35=1161` `no_tier_match=48` `exp_max_low=1019`

## Already applied earlier today (skip — do not re-apply)

Original morning second pass (listings gone from `/findjobs`):

| ID | Title | Company |
|----|-------|---------|
| `6a1fd51dd7bf645877d57db8` | Principal Engineer, Salesforce Health Cloud | Unique Occupational (38L) |
| `6a4b58ed80b936a4374760b4` | Senior Full-Stack Engineer | Recro (38L) |
| `6a2146d3654875adb93e1546` | Sr. AI Ops Engineer | Fx31labs (45L) |

Earlier same-day re-run after an in-session stretch (not on current `main` filters; do not re-apply):

| ID | Title | Company |
|----|-------|---------|
| `6a7edbb660bd287cdd75f584` | Devops/ Platform Engineer | Cutshort Lightning (80L) | <!-- pragma: allowlist secret -->
| `6a2bf99d308c1234359cc547` | Senior AI/ Machine Learning Engineer | Cliply Pte Ltd (55L) |
| `6a450a142b6b3e267b5d0108` | AI Engineer | J&F (50L) |
| `6a7063062f3b4edf544086b6` | Audio AI Engineer | Recruiting Bond (50L) |
| `6a7b71f0d9f0ecab30edf2f5` | AI Engineer | Sentiaflow (40L) |
| `69fac46a0d641e613a54e248` | Copilot Developer | Aheadrace Software Developement Services Pvt Ltd. (40L) |
| `6a0ac05203b6263fd2c59533` | POD Lead | Ampera Technologies (40L) |
| `69ccdeeec7eecac76c792578` | DevOps Engineer | Mactores Cognition Private Limited (35L) |

## Why 0 new applies
Remaining Hyd/remote Architect / Tech Lead / EM / Senior .NET cards list **max CTC 12–25 LPA** (hard-skip under 35L). `ctc>=35` leftovers are title-first wrong fits (same inventory the prior #163 re-run inspected). No new Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET card at ≥35L.

#164 ATS brochure/false-CTA fail-fast was loaded but unused — zero qualifying externals.

Did **not** loosen the 35L floor or widen title filters (that would invent wrong-fit applies). Did **not** launch another post-fix re-run (no new code-fixable blocker; same-day portal re-run count is **5/5** including this job).

## Applied
_None this pass_

## Questionnaires
- No new pending screening submitted (41 already-submitted; 3 non-questionnaire awaiting threads skipped).
- Historical `locked-empty`: 322 (cannot be unlocked in code).

## Failed applies
_None_

## Email
Portal status mailed via Resend MCP to the documented job-status recipient (id `a41bdc00-733d-489d-b2d3-418d4cd7f888`). `RESEND_FROM_EMAIL` unset — used documented fallback `Job Status <onboarding@resend.dev>`.

Artifacts: `/opt/cursor/artifacts/` portal daily-run JSON and `/tmp/` run `stats.json`
