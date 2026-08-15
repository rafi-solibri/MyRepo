# Naukri daily — 2026-08-15 (post-fix re-run, PR #160 code)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
This run: https://cursor.com/agents/bc-e4e699b4-df00-4ba1-b7ae-7e0692af3c87
`POST_FIX_RERUN=1` on `main` `ce373d6` (`fix(ats): complete company-website applies…` #160), then in-session re-exec after CTA fix `dc3f645`.

## Profile resume refresh (STEP 0)
- **ok** — `profileUpdated: true`
- Resume filename shown: **Rafi_Resume.docx**
- Update text: **Uploaded today**
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

## Counts (in-session re-run with CTA fix)
| | |
| --- | --- |
| profileUpdated | true |
| applied (this run) | **0** |
| externalCompleted | 0 |
| blocked | 0 |
| skipped | 3411 |
| seen | 194 |

Pass 1 on merged #160 (before CTA fix): applied 0 · external 0 · blocked 1 · skipped 3410 · seen 194.

## Applied this run
None confirmed. Do not invent applies.

## Already applied (skipped today)
- i2e Consulting — Solution Architect — Naukri — `Rafi_Resume.docx` — https://www.naukri.com/job-listings-solution-architect-i2e-consulting-remote-9-to-15-years-130826013685
- Clean Harbors — .Net Fullstack Tech Lead — Naukri — `Rafi_Resume.docx` — https://www.naukri.com/job-listings-net-fullstack-tech-lead-clean-harbors-hyderabad-10-to-14-years-230226023126

Earlier same-day post-fix re-run (`bc-23b4a9a3…`, pre-#160): Xanika Infotech — PROS CPQ Solution Architect (Naukri Quick Apply).

## Blocked
- Pass 1 only: Capgemini — Enterprise Architect — Hyderabad — Naukri — `apply_unconfirmed` — CTA was **View applied jobs (20+)** (nav chrome, not the job button).
- Pass 2: Capgemini Enterprise Architect no longer in recommended inventory (no second confirmation). Direct URL retry hung on CDP; not counted.

## Code fix (new blocker this run)
`has-text('Apply')` matched recommended-jobs **View applied jobs (20+)**. Branch `cursor/naukri-fix-view-applied-jobs-cta-a239` commit `dc3f645`. GitHub `gh pr create` is not permitted in this environment; PR is pending owner approval via Cursor.

Post-fix cloud re-runs for Naukri on 2026-08-15 IST: **2/5** (this job). Did not launch another cloud agent.
