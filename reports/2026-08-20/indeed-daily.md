# Indeed daily — 2026-08-20 (post-fix re-run)

Source: cloud WARP + SeleniumBase UC (`cloud-warp-uc`) on merged `#219` (`db49e3c`) then feature-branch retries  
Resume: `resumes/Rafi_Resume.docx` (Expected 65 LPA / Current 52 LPA; Hyd + Remote)  
Preflight: WARP SOCKS + UC Turnstile (`uc_gui_click_cf_retry`) → **exit 0**. Session restored via Account settings.

## Totals (unique Easy Apply submitted today)

| Metric | Pass 1 (`#219`) | Pass 2 (this branch) |
| --- | ---: | ---: |
| Applied (Easy Apply submitted) | 3 | 2 |
| External ATS completed | 0 | 0 |
| Rejected / incomplete | 4 | 6 |
| Seen | 69 | 93 |

No invented applies. Pass 2 skipped 13 already-applied listings (including pass 1 submits).

## Applied (Easy Apply)

1. **Binarry Stitchh** — Senior .NET C# Engineer – Elasticsearch — Remote
2. **Prahartech** — Principal Enterprise AI Architect – Strategic Advisory & Governance — Remote
3. **SIM RETAIL SOLUTIONS** — Senior .NET Developer – Azure DevOps & AI-Assisted Development — Remote
4. **Kasmoprav** — Sr. FDE – Resident Solution Architect — Remote
5. **Prana Life Science** — Veeva Vault RIM – Technical Lead / Architect — Remote

## Rejected / incomplete Easy Apply (still stuck)

- **ValGenesis** — Senior Software Engineer, Fullstack — education combobox still `Select an option` after JS fill (`Choose an option to continue.`)
- **LTIMindtree** — Senior Principal - Architecture — Title * Mr./Ms. questions-module
- **UST** — .Net Fullstack Developer — questions-module (Phone No / Date)
- **CoverGo** / **OneMetric** — questions-module incomplete on pass 2

## Blocked (company ATS / infra)

Mostly `external_incomplete_or_timeout` / `no_ats_form` / WARP SOCKS `Page.goto` failures. Mid-run `secure.indeed.com/auth?from=bot-detection-anonymous` was skipped as `title_not_target` until URL/title login-wall detection.

## Code fixes (branch `cursor/indeed-fix-education-combobox-20260820`)

- Education combobox: label scan, document-level options, pointer events + SeleniumBase click for Bachelor's.
- Detect `secure.indeed.com/auth` / bot-detection **before** `skip_reason`; restore session.

`gh pr create` was denied (`Resource not accessible by integration`). Branch is pushed for owner merge.
