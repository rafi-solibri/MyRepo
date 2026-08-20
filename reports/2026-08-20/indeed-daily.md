# Indeed daily — 2026-08-20 (post-fix re-run)

Source: cloud WARP + SeleniumBase UC (`cloud-warp-uc`) on merged `#219` (`db49e3c`)  
Resume: `resumes/Rafi_Resume.docx` (Expected 65 LPA / Current 52 LPA; Hyd + Remote)  
Preflight: WARP SOCKS + UC Turnstile (`uc_gui_click_cf_retry`) → **exit 0**. Session restored via Account settings.

## Totals

| Metric | Count |
| --- | ---: |
| Applied (Easy Apply submitted) | 3 |
| External ATS completed | 0 |
| Rejected / incomplete | 4 |
| Blocked | 31 |
| Skipped | 33 |
| Seen | 69 |

No invented applies. 10 already-applied listings were skipped.

## Applied (Easy Apply)

1. **Binarry Stitchh** — Senior .NET C# Engineer – Elasticsearch — Remote
2. **Prahartech** — Principal Enterprise AI Architect – Strategic Advisory & Governance — Remote
3. **SIM RETAIL SOLUTIONS** — Senior .NET Developer – Azure DevOps & AI-Assisted Development — Remote

## Rejected / incomplete Easy Apply

- **ValGenesis** — Senior Software Engineer, Fullstack — education combobox left on Select an option (`Choose an option to continue.`)
- **LTIMindtree** — Senior Principal - Architecture — questions-module incomplete
- **UST** — .Net Fullstack Developer — questions-module incomplete
- **ValGenesis** — Senior Software Engineer, Database — questions-module incomplete

## Blocked (company ATS / infra)

Mostly `external_incomplete_or_timeout` / `no_ats_form` / SOCKS `Page.goto` failures through WARP. Two search_blocked; two CAPTCHA/bot wall. Run ended on `Sign In | Indeed Accounts` (`from=bot-detection-anonymous`) misclassified as `title_not_target`.

## Code fixes (branch `cursor/indeed-fix-education-combobox-20260820`)

- Fill SmartApply highest-degree combobox (colon labels; portaled `[role=option]`).
- Detect mid-run Sign-in wall **before** `skip_reason`.

`gh pr create` was denied for this integration (`Resource not accessible by integration`). Branch is pushed for owner merge / `auto-merge-fix-pr.sh`.
