# Naukri Home Daily — 2026-08-14

Candidate: Mohammed Abdul Rafi Ahmed | Resume: `Rafi_Resume.docx` | Expected 65 LPA / Current 52 LPA | Hyd + Remote  
Source: **home-local** (Windows residential, `CHROME_CDP_MODE=system`)

## STEP 0 — Profile resume refresh
- **profileUpdated:** `true`
- **verify:** Uploaded today (`Rafi_Resume.docx` — matched token `today`)
- Preflight SQLite cookies locked / no `nauk_rt` (ABE) — continued after **live CDP** (`live_cdp_naukri_ok`)

## Counts
- profileUpdated: **true**
- applied: **4**
- externalCompleted: **0**
- blocked: **5**
- skipped: **3510** (seen 198)
- expandedAges: `[15, 30, 60]` + extra .NET/Azure queries (applied stayed &lt; 8)

## Applied (Naukri Quick Apply)
| Company | Role | Location |
| --- | --- | --- |
| HUCON Solutions | Solution Architect - Azure Data Factory - Hyderabad | Hyderabad |
| People Tech Technology | Embedded Technical Architect- SME | Hyderabad |
| Tata Consultancy Services | TOSCA Automation Architect | Hyderabad, Noida, Mumbai |
| Hiring for a Software Product company | Artificial Intelligence Architect | Remote |

## External ATS completed
_None confirmed this run (no invented applies)._

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| People Tech Technology | Embedded Technical Architect | `quick_apply_not_found` | Naukri |
| Jade Global | Lead AI Engineer with Python (.Net or JAVA) | `apply_unconfirmed` | Naukri |
| PwC | Technical Lead - Manager | `apply_unconfirmed` | Naukri |
| Vidaxl | Technical Lead | `external_incomplete_or_timeout` | company_ATS |
| Wood Plc | Principal Project Controls Engineer | `external_incomplete_or_timeout` | company_ATS |

## Skip reasons (sample of first 40)
- duplicate_in_run: 30
- skip_title_keyword: 5
- skip_seniority: 3
- skip_no_dotnet: 1
- already_applied_detail: 1

## Code fixes this run
- Dual-write Naukri artifacts to repo `artifacts/` + `C:\opt\cursor\artifacts` (`tools/artifact_path.js`) — Node `/opt` ≠ Git Bash `/opt` on Windows, so home publish could miss the fresh JSON.
- Title skips: TOSCA / Embedded / Artificial Intelligence Architect (`resume_and_filters.js`).

## Artifacts
- `artifacts/naukri-daily-apply.json`
- `artifacts/naukri-daily-run.json`
- `~/.cursor/portal-home-logs/naukri/naukri-daily-run.json`
- `reports/2026-08-14/naukri-home-daily.md`
