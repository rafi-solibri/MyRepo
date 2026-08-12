# Naukri Home Daily — 2026-08-12

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` | Expected 65 LPA / Current 52 LPA | Hyd + Remote  
Source: **home-local** (Windows residential, `CHROME_CDP_MODE=system`)

## STEP 0 — Profile resume refresh
- **profileUpdated:** `true`
- **verify:** Updated today
- Preflight SQLite reported cookies locked / no `nauk_rt` (Chrome open) — continued after **live CDP** homepage probe (`hasAuth: true`)

## Counts
- profileUpdated: **true**
- applied: **0**
- externalCompleted: **0**
- blocked: **9**
- skipped: **2604** (seen 291)
- expandedAges: `[15, 30]`

## Applied / External
_None confirmed this run (no invented applies)._

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Blue Yonder | Enterprise Architect - Innovation | `external_incomplete_or_timeout` | Workday |
| RSM US in India | Solution Architect Manager 2 | `external_incomplete_or_timeout` | Workday-branded |
| Texas Instruments | Solutions Architect | `external_incomplete_or_timeout` | Oracle Cloud |
| Arcesium | Principal Engineer - SRE | `external_incomplete_or_timeout` | Greenhouse |
| Nagarro | Associate Principal Engineer, IOT | `external_link_not_opened` | company_ATS |
| Techy Geeks | Databricks Architect - AWS | `external_link_not_opened` | Hirist “Apply attempted” |
| Apple | SRE Engineering Manager | `external_incomplete_or_timeout` | Apple jobs |
| Arcesium | Senior Principal Engineer - Backend | `external_link_not_opened` | Hirist “Apply attempted” |
| Mancer Consulting | Engineering Manager - Platform | `external_link_not_opened` | Hirist “Apply attempted” |

## Skip reasons (top)
- duplicate_in_run: 2279
- already_applied_detail: 157
- skip_title_keyword: 77
- skip_seniority: 45
- skip_no_dotnet: 34
- skip_ctc_max_30: 7
- skip_location: 2
- skip_ctc_max_31: 1
- already_applied: 1
- skip_ctc_max_32.5: 1

## Code fix (this home run)
- Branch: `cursor/naukri-fix-home-cdp-hirist-sre-a239`
- Live CDP waiter `tools/naukri/wait_for_cdp_login.js` + `chrome_session` / `home-headed-login` wiring (Windows ABE / locked Cookies DB)
- Soft-skip Hirist CTA “Apply attempted” (do not hard-block)
- Skip SRE/DevOps-primary titles; prefer repo `resumes/Rafi_Resume.docx` on Windows
- Workday: stronger cookie dismiss, Autofill→Manual fallback, detect Workday UI on branded hosts

## Artifacts
- `artifacts/naukri-daily-run.json`
- `artifacts/naukri-daily-apply.json`
- `~/.cursor/portal-home-logs/naukri/naukri-daily-run.json`
