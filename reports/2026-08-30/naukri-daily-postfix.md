# Naukri Daily — same-day post-fix re-run 2026-08-30 IST

Ran on `main` at `fa8b17f` (#293) with `POST_FIX_RERUN=1`. Did not invent applies. Skipped jobs already applied today.

## STEP 0 — profile resume

- **ok / profileUpdated:** true
- **file:** `Rafi_Resume.docx` (rebuilt from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx`)
- **verify:** Uploaded today
- **updateOn:** (empty — today-token path)
- Artifact: `/opt/cursor/artifacts/naukri-profile-resume.json`
- Canonical CV restored on profile at end of run

## Applies this re-run

| Company | Role | Path | Resume | Outcome |
| --- | --- | --- | --- | --- |
| Valuelabs | Azure Platform Architect | Naukri Quick Apply | tailored `Rafi_Resume.docx` | Worker: `apply_unconfirmed`. **Post-verify CTA = Applied** (`300826004443`) |
| Blackbaud | Software Engineer, Principal - .NET DevOps | Workday ATS | tailored `Rafi_Resume.docx` | **blocked** `ats_password_policy` |

Morning run already applied TCS Azure Cloud Solutions Architect (`290826008626`) — not re-applied (not in this inventory).

## Counts

| | Worker JSON | After CTA verify |
| --- | ---: | ---: |
| profileUpdated | 1 | 1 |
| applied | 0 | **1** (ValueLabs) |
| external | 0 | 0 |
| blocked | 2 | 1 (Blackbaud) |
| skipped | 2959 | 2959 |
| seen | 212 | 212 |

Combined day with morning TCS: **applied = 2**.

## Blockers / fix

- ValueLabs JD is Azure landing-zone/IaC (Terraform, Backstage) — not .NET. Title-skip + `confirmApplied` reload after empty CTA pushed on `cursor/naukri-daily-post-fix-re-run-2026-08-30-2d3e`.
- Blackbaud: owner must reset `NAUKRI_WORKDAY_PASSWORD` (12+ complexity).
- Hirist login walls: skipped (3).
- Thin Hyd/.NET SA/Lead inventory after existing title/CTC filters; early-expand 3/7 + 15/30/60 + extra queries ran.

## Artifacts

- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-postfix-2026-08-30-summary.json`
- `/opt/cursor/artifacts/naukri_valuelabs_applied_cta.png`
- `/opt/cursor/artifacts/naukri_profile_uploaded_today.png`
