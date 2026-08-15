# Foundit daily — 2026-08-15 (POST_FIX_RERUN=1 on merged #164)

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT OK; `/home/ubuntu/.config/chrome-foundit`)
- Resume: `resumes/Rafi_Resume.docx` (verified; never stubbed)
- HEAD at apply start: `586c376` — `fix(ats): fail-fast brochure pages and false Apply CTAs` (#164)
- Applied tab: **457 → 489** (+32 this session; earlier same-day runs already moved the tab before 457)
- Pass 1 (`#164` only): +12 Falcon applies, then stopped to patch EXTRA_QUERIES false titles
- Pass 2 (filter fix `c507e25`): **470 → 489** (+19); 82 already-applied skipped; inventory exhausted through 3650-day window
- Artifacts: `/opt/cursor/artifacts/foundit-apply-report.json` (pass 1), `/opt/cursor/artifacts/foundit-apply-report-pass2.json` (pass 2)
- No `canJobApply` dry-run calls
- #164 fail-fast observed: DTCC Oracle Cloud `job_unavailable`; Jacobs careers `no_ats_form` (no 6.5m brochure timeout)

## Applied — pass 1 (merged #164, pre-filter-fix)
1. **Allianz Technology** — Solution Architect (m/f/d) — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `linkedin_no_easy_apply` — Thailand | remote
2. **hire feed** — AI Solution Architect — LinkedIn `linkedin_no_easy_apply` — UAE | Remote *(false apply — skipped on pass 2)*
3. **Penbrothers** — Senior Solutions Architect — Foundit Falcon `NORMAL` — Philippines | remote
4. **Reap** — Data Engineering Manager — LinkedIn `linkedin_no_easy_apply` — Singapore | Remote *(false apply — skipped on pass 2)*
5. **Shell** — Facilities Engineering Manager — LinkedIn `linkedin_no_easy_apply` — Singapore | remote *(false apply — skipped on pass 2)*
6. **Oracle** — Oracle Fusion Apps Principal Solutions Engineer (ERP) — LinkedIn `linkedin_no_easy_apply` — Saudi Arabia | remote *(false apply — skipped on pass 2)*
7. **Celestica** — Operations Engineering Manager 2 — LinkedIn `linkedin_no_easy_apply` — Thailand | Remote *(false apply — skipped on pass 2)*
8. **Jacobs** — Principal Electrical Engineer - Power Generation — LinkedIn `linkedin_no_easy_apply` — Philippines | remote *(false apply — skipped on pass 2)*
9. **Allianz Technology** — Principal DevOps Engineer (m/f/d) — LinkedIn `linkedin_no_easy_apply` — Thailand | WFH
10. **Arcadis** — Principal Engineer - Mechanical (UK Water) — LinkedIn `linkedin_no_easy_apply` — Hyderabad *(false apply — skipped on pass 2)*
11. **RealPage** — Application Architect — Foundit Falcon `NORMAL` — Hyderabad
12. **realpage, inc.** — Application Architect — LinkedIn `linkedin_no_easy_apply` — Hyderabad

## Applied — pass 2 (after non-software / Oracle Fusion / AI-data title skips)
1. **Red Hat** — Specialist Solution Architect - OpenShift and AppServices — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
2. **Red Hat** — Red Hat Enterprise Linux Specialist Solution Architect — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
3. **Red Hat** — AI Specialist Solution Architect, SEA — LinkedIn `linkedin_no_easy_apply` — Singapore | remote *(follow-up skip added after this pass)*
4. **Sonata Software** — Solution Architect Security — Foundit Falcon `NORMAL` — Malaysia | Remote
5. **Red Hat** — OpenShift Account Solution Architect - Ecosystem — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
6. **Red Hat** — OpenShift Senior Specialist Solutions Architect — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
7. **SAS** — SAS Cloud Technical Architect (ASEAN) — LinkedIn `linkedin_no_easy_apply` — Thailand | Remote
8. **AVEVA** — Technical Lead - Process Optimization Software — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
9. **Tribal Group** — Associate Technical Lead — LinkedIn `linkedin_no_easy_apply` — Malaysia | Remote
10. **beyondsoft singapore** — Software Technical Lead — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
11. **IBM** — Application Architect-zOS — Foundit Falcon `NORMAL` — Hyderabad
12. **realpage, inc.** — Application Architect (Oracle Subscription Management) — LinkedIn `linkedin_no_easy_apply` — Hyderabad
13. **Red Hat** — Edge Specialist Solution Architect — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
14. **Red Hat** — OpenShift Specialist Solutions Architect — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
15. **Allianz Technology** — Solution Architect - Mobile Applications — LinkedIn `linkedin_no_easy_apply` — Thailand | remote
16. **DTCC** — Principal Application Architect (Architecture Governance) — Foundit Falcon + Oracle Cloud ATS `job_unavailable` — Hyderabad
17. **Orange Business Services** — Cloud Solution Architect — LinkedIn `linkedin_no_easy_apply` — Singapore | remote
18. **GitLab** — Senior Professional Services Technical Architect, META — LinkedIn `linkedin_no_easy_apply` — UAE | remote
19. **Jacobs** — Engineering Manager, Water — Foundit Falcon + careers `no_ats_form` — Singapore | remote *(follow-up skip added after this pass)*

## Top skip reasons (pass 2)
- no .NET on title+skills: 344
- location Bengaluru / Pune / Noida / Chennai / others: majority of remainder
- no seniority keyword on title: 109
- junior/mid maxExp bands: 53
- SAP without .NET: 35
- **new** non-software engineering without .NET on title: 12
- **new** pure AI/data without .NET on title: 11
- infra/ops without .NET on title: 9
- **new** Oracle Fusion/ERP without .NET on title: 4
- already applied today (duplicates): 82

## LinkedIn referral drafts
1. RealPage — Application Architect (Hyderabad, Falcon `NORMAL`)
2. IBM — Application Architect-zOS (Hyderabad, Falcon `NORMAL`)
3. Sonata Software — Solution Architect Security (Falcon `NORMAL`)

## Filter fix
- Branch `cursor/foundit-daily-post-fix-re-run-2026-08-15-b13b`
- `skipTitleReason`: facilities/electrical/mechanical/civil/water, operations engineering manager, Oracle Fusion/Apps/ERP, AI Solution / AI Specialist Architect, data engineering (Naukri parity) when `.NET` is not on the title
- Tests: `node tools/foundit/filters.test.js` OK
- Pass 2 confirmed the first-wave skips (Shell Facilities, Jacobs Electrical, Arcadis Mechanical, Celestica Ops EM, Oracle Fusion, hire feed AI Solution, Reap Data Engineering)
