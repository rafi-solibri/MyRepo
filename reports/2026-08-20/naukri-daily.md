# Naukri daily — 2026-08-20 IST

Post-fix re-run on merged `main` (PR [#217](https://github.com/rafi-solibri/MyRepo/pull/217) Mainframe/COBOL skip). Resume: `resumes/Rafi_Resume.docx`.

## STEP 0 — profile resume refresh

- **This re-run:** ok — `profileUpdated: true`, `matchedToken: today`
- Resume shown: `Rafi_Resume.docx` / “Uploaded today”
- Headline touch: skipped (`headline_input_missing`)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`

Morning run also refreshed successfully (`Uploaded today`).

## Combined applies today (do not double-count)

Valid Naukri Quick Apply (morning, before this re-run):

1. **Epam Systems** — Solution Architect — Naukri — `Rafi_Resume.docx` — https://www.naukri.com/job-listings-solution-architect-epam-systems-hyderabad-10-to-20-years-190826021515
2. **Accordion Partners** — Technical Director | Hyderabad — Naukri — `Rafi_Resume.docx` — https://www.naukri.com/job-listings-technical-director-accordion-partners-hyderabad-11-to-21-years-190826032569

False-apply (morning; now skipped by #217):

3. **Netm Corporate Solutions** — Mainframe Developer | Senior Mainframe Developer | Mainframe Architect — Naukri — https://www.naukri.com/job-listings-mainframe-developer-senior-mainframe-developer-mainframe-architect-netm-corporate-solutions-hyderabad-bengaluru-india-10-to-20-years-190826025391

**This re-run applied: 0** (did not invent applies). Already-applied skipped here: i2e Consulting Solution Architect, Clean Harbors .Net Fullstack Tech Lead.

## This re-run counts

| Metric | Count |
| --- | --- |
| profileUpdated | true |
| applied | 0 |
| external completed | 0 |
| blocked | 6 |
| skipped | 2272 |
| seen | 243 |

Ages: 1 → early 3,7 → expand 15,30,60 + extra .NET/Azure queries. Thin remaining Hyd/.NET inventory after morning applies.

## Blocked this re-run

| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Sprinto Hq | Senior Manager, Delivery Partnerships | `external_incomplete_or_timeout` | Lever ATS |
| Highlevel Llc | Staff Product Manager - Agency Revenue Growth | `external_incomplete_or_timeout` | Lever ATS |
| Solutionzhere | CE Functional Lead/Architect | `external_link_not_opened` | company_ATS (empty CTA) |
| A5E Consulting | OTC Data Migration Architect | `external_link_not_opened` | company_ATS |
| A5E Consulting | OTC Brim Lead Architect | `external_link_not_opened` | company_ATS |
| Mancer Consulting Services | Engineering Manager - Platform (10-15 yrs) | `external_link_not_opened` | company_ATS (empty CTA) |

## Code fix this re-run

Staff/Senior Manager **Product Manager** and **Delivery Partnerships** were attempted because `staff` / `senior manager` match the arch-lead waiver. SAP **OTC BRIM** / OTC Data Migration architects were attempted because `sap` was not in the title. Company-site jobs with empty detail CTA (`external_link_not_opened`) never waited for the company-site button (waiter only accepted Quick apply / Applied).

Follow-up PR skips those titles and waits/retries company-site CTAs so Platform EM (Mancer) can open ATS.

## Artifacts

- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- `/workspace/artifacts/naukri-daily-apply.json`
