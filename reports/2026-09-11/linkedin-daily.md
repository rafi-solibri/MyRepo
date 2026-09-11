# Daily apply — 2026-09-11

## Status
**COMPLETE** for this session. Restriction lift (2026-09-10T03:37:00Z) had cleared. Google SSO + owner 2FA earlier in the day; feed/`li_at` live. **Do not invent applies** — counts below are log-confirmed `Application submitted` / ATS confirmation only.

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted (confirmed) | **24** (18 on-profile; 6 false applies called out) |
| External / ATS completed (confirmed) | **0** |
| Easy Apply skipped (restart process) | **639** |
| Easy Apply blocked (unique jobs) | **8** |
| External ATS blocked | **23** |
| External ATS skipped | **17** |

Target was 40–50+ Easy Applies. Inventory thinned after 24h / 3d / 7d / 14d Easy Apply and non–Easy Apply passes. Helper `MAX_APPLY` was not the limiter.

## Confirmed Easy Apply submitted

### On-profile
| Company | Title | Location | Job ID |
| --- | --- | --- | --- |
| Talentgigs | Technical Lead | Hyd | 4464831458 |
| Marriott Tech Accelerator | Senior Engineering Manager - FinOps / Cloud Cost Optimization | Hyd | 4465653225 |
| Astreya | Endpoint Management Architect | Hyd | 4464556569 |
| Simplify Alpha | Delivery Architect | Hyd | 4463342397 |
| Weekday AI (YC W21) | Principal Architect (Security) | Hyd | 4465632909 |
| IndusGuru Network Partners | Cloud Infrastructure & Platform Automation Architect (Remote / US shift) | India Remote | 4464848337 |
| Sourcebae | Solutions Architect | India Remote | 4465650081 |
| TIGI HR | Cloud Architect – Azure & AWS | India Remote | 4464517129 |
| Jobgether | Engineering Manager - System Design | India Remote | 4464504384 |
| Ivycornersearch | Information Technology Architect | Hyd | 4463952411 |
| Weekday (YC W21) | Principal Architect (Security) | Hyd | 4463461192 |
| OpsMx | Product Engineering Manager - AI & Application Security | India Remote | 4463004099 |
| Luxoft | Insurance Solution Architect | India Remote | 4465029970 |
| Jobgether | Senior Engineering Manager | India Remote | 4462955728 |
| Jobgether | Engineering Manager - Linux Hardware Enablement | India Remote | 4461946478 |
| Jobgether | Engineering Manager - Security Standards and Hardening | India Remote | 4461130636 |
| The Hartford | Engineering Manager | Hyd | 4462674372 |
| Turing | Remote Software Engineer – C# | India Remote | 4464865020 |

Turing C# is on-stack but IC (below the usual architect/EM target).

### False applies (submitted; filters patched after)
| Company | Title | Why false | Job ID |
| --- | --- | --- | --- |
| Zigsaw | Business Development Manager | TITLE_OK matched bare development manager | 4464854439 |
| Tek Grove | Dell Boomi Architect | iPaaS / Boomi not on blacklist yet | 4465633831 |
| Sagility | Associate Director Training | bare director + training | 4466049000 |
| Latinem Private Limited | Senior Concept Architect | AEC building-design | 4466058044 |
| Us Design Studio | Junior Architect (1-2 years) | junior AEC | 4463943681 |
| Turing | Remote Senior Software Engineer – Python | Python-primary SWE | 4464865028 |

## Easy Apply blocked (not applies)
| Company | Title | Reason | Job ID |
| --- | --- | --- | --- |
| Cyara | Senior Engineering Manager | exceeded Easy Apply steps (twice; Next-recovery not in this process) | 4461107562 |
| Studio Infinite | Senior Project Architect - High-Rise / Mivan / BIM | exceeded steps (AEC; later blacklisted) | 4463494383 |
| Moniepoint Group | Head of Engineering, Sales & Marketing Tools | exceeded Easy Apply steps | 4464198750 |
| HYR Global Source Inc | ETRM Solution Architect (Endur, Azure) | exceeded Easy Apply steps | 4466053163 |
| Coinbase | Engineering Manager - Customer Experience AI | exceeded Easy Apply steps | 4427024421 |
| BAY6.AI | Artificial Intelligence Engineering Lead | exceeded Easy Apply steps | 4464859010 |
| Moniepoint Group | Head of Engineering, POS Application Platform | Easy Apply time-cap timeout | 4426098593 |

## External / company-site
`python3 tools/*/…_external_apply.py` finished **submitted=0**, blocked=23, skipped=17.

Typical ATS outcomes (not applies): Workday login walls (Palo Alto/CyberArk, ModMed), iCIMS/BambooHR CAPTCHA, Perficient OTP wall, Greenhouse/Phenom/Hirist incomplete or no form (Wipro, Softobiz, Hire Feed, Microsoft PEM, Cognizant, Planful, PepsiCo, Jacobs Data Centre, EY Noida URL).

EY DevOps Architect careers URL was **Noida** despite a Hyd card — timed out; not counted.

## Code fixes on this branch (not merged while the helper was the only applier)
- Skip AEC concept architect; junior architect / 1–2 year titles; Python-primary SWE titles
- Skip training / generic Director; Boomi; restaurant/project/high-rise/Mivan architects; bare development manager
- Recover Next/Submit when Apply chrome has no modal class (Cyara / Moniepoint / Coinbase class)
- Keep India-remote jobs past view location recheck; do not treat pipe-delimited titles as location
- Salary / location-in-India answers; persist submitted IDs only

Issues: `automation-prompts/issues/` portal log for 2026-09-11.

## False-skip notes (fixed mid-run; some only after restart)
- IndusGuru Remote/US shift and Sourcebae India Remote were first skipped, then submitted after location-parse + `remote_search` view recheck
- Quik Hire “Cloud Solutions Architect (Hybrid)” still parsed title-as-location in this process
- Company-name-as-location (Technogen, TJX India, D.E. Shaw) still false-skipped some view rechecks

## Artifacts
- `/opt/cursor/artifacts/*easy-apply.log`
- `/opt/cursor/artifacts/apply-report.json` (restart process only: submitted 17)
- `/opt/cursor/artifacts/*external-apply.log`
- `/opt/cursor/artifacts/external-apply-report.json`

## Owner / next
1. Merge this branch so Next-recovery + title filters land on `main`, then same-day re-run can retry Cyara / Coinbase / Moniepoint / HYR (fill-step blocks were not persisted as seen IDs)
2. ATS CAPTCHA/login walls need owner cookies or a solver key; do not invent those as applies
3. People-search referrals stay off (portal `*_PEOPLE_REFERRALS=0`)
