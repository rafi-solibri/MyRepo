# Naukri daily — 2026-08-20 IST

Post-fix re-run on merged `main` (PR [#217](https://github.com/rafi-solibri/MyRepo/pull/217) Mainframe/COBOL skip). Resume: `resumes/Rafi_Resume.docx`.

## STEP 0 — profile resume refresh

- **ok** — `profileUpdated: true`, `matchedToken: today`
- Resume shown: `Rafi_Resume.docx` / “Uploaded today”
- Headline touch: skipped (`headline_input_missing`)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

Morning run also refreshed successfully (`Uploaded today`).

## Combined applies today (do not double-count)

Morning (before this re-run; Naukri Quick Apply, `Rafi_Resume.docx`):

1. **Epam Systems** — Solution Architect — https://www.naukri.com/job-listings-solution-architect-epam-systems-hyderabad-10-to-20-years-190826021515
2. **Accordion Partners** — Technical Director | Hyderabad — https://www.naukri.com/job-listings-technical-director-accordion-partners-hyderabad-11-to-21-years-190826032569

False-apply morning (now skipped by #217):

3. **Netm Corporate Solutions** — Mainframe Developer | Senior Mainframe Developer | Mainframe Architect — https://www.naukri.com/job-listings-mainframe-developer-senior-mainframe-developer-mainframe-architect-netm-corporate-solutions-hyderabad-bengaluru-india-10-to-20-years-190826025391

This re-run (after #217 + in-session filter/CTA fix):

4. **Techstar Group** — Azure Senior DevOps Architect — Hyderabad — Naukri — `Rafi_Resume.docx` — CTA `view_applied_jobs` — https://www.naukri.com/job-listings-azure-senior-devops-architect-techstar-software-development-india-pvt-ltd-hyderabad-10-to-15-years-310726924667 — **devops-primary; skip added so this band is not applied again**

Already-applied skipped (not re-counted): i2e Consulting Solution Architect, Clean Harbors .Net Fullstack Tech Lead.

External completed: **0**.

## Counts

### Pass 1 (merged #217 only)

profileUpdated true / applied 0 / external 0 / blocked 6 / skipped 2272 / seen 243

Blocked: Sprinto Delivery Partnerships (Lever timeout), Highlevel Staff Product Manager (Lever timeout), Solutionzhere CE Functional Lead (`external_link_not_opened`), A5E OTC Data Migration + OTC Brim (`external_link_not_opened`), Mancer EM-Platform (`external_link_not_opened`).

### Pass 2 (PM/OTC skip + company-site CTA retry)

profileUpdated true / applied 1 / external 0 / blocked 3 / skipped 3087 / seen 221

Blocked: Aveva R&D Senior Member of Technical Staff (`apply_unconfirmed`), Wells Fargo Lead Software Engineer (`ats_login_wall` Workday), TCS Cloud Network Architect (`apply_unconfirmed`).

Mancer Engineering Manager - Platform: `hirist_login_required_skip` (owner Desktop Hirist login optional). Product Manager titles skipped via `skip_title_keyword`.

Ages: 1 → early 3,7 → expand 15,30,60 + extra .NET/Azure queries.

## Code fixes this re-run (pushed, PR create blocked for this integration)

- `SKIP_TITLE_RE`: product manager, delivery partnerships, brim, OTC data migration/BRIM, devops architect, network architect
- `waitForVisibleApplyCta` + `handleExternal` retry company-site CTA (empty CTA was dropping ATS)
- Tests: `node tools/naukri/test_filters.js` OK
- Branch: `cursor/naukri-daily-post-fix-re-run-2026-08-20-a82b`

## Artifacts

- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/opt/cursor/artifacts/naukri-daily-apply-postfix-1.json` (pass 1)
- `/opt/cursor/artifacts/naukri-daily-apply.json` (pass 2)
- `/workspace/artifacts/naukri-daily-apply.json`
