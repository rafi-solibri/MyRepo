# Hitech City / Knowledge City daily — 2026-08-15 (career portals)

## Status
**Careers passes completed** — 0 new confirmation applies this session. LinkedIn skipped (CAPTCHA/checkpoint). Boards skipped (careers-only).

## Totals (final careers pass)
- Career ATS submitted: **0**
- Hyland iCIMS: **6 Hyd architect JDs extracted** including **Senior Software Architect - .NET** (Hyderabad hybrid). Apply opens GDPR email + **hCaptcha** (owner-only). Fail-fast CAPTCHA in ~37s for 4 jobs (company wall cap) — no more 6×390s timeouts.
- Other guest boards: Intel/JPMC/Oracle/AMD titles were hardware, Java, or non-Hyd. Blue Yonder Phenom search now loads (TMS architect skipped: not Hyd).
- CAPTCHA boards (Experian / Blackbaud / Palo Alto) ranked later; still owner DataDome/reCAPTCHA.

## Applied
None this session (confirmation text only). Earlier same-day cloud run already submitted **Solera JR-019000** (Workday).

## Blockers fixed this run (will not repeat)
| Issue | Fix |
| --- | --- |
| Instahyre autofix never launched Chrome (`ECONNREFUSED`) | `run-portal-with-autofix.sh` launches CDP (#171) |
| Hyland/Intel/JPMC `jobCount: 0` — iCIMS parent chrome filled the 40-link cap | Extract job-id/path slugs only; scan `in_iframe=1` first (#172) |
| Hyland Apply timed out on parent chrome; 6× ATS cap | Click iframe `mode=apply`; fail-fast hCaptcha login (#173) |
| Phenom Taleo search URLs bounced to `/us/en` | Blue Yonder / Fiserv `search-results` URLs |
| CAPTCHA boards scanned first and starved guest ATS | Rank SmartRecruiters/Blackbaud/PAN later |

## Owner-only (cannot fix in code)
- LinkedIn `/checkpoint/challenge` — `bash scripts/home-headed-login.sh linkedin` + Save snapshot
- Hyland iCIMS **hCaptcha** on Apply (Senior Software Architect .NET, Hyderabad)
- Experian / Blackbaud / Palo Alto DataDome or reCAPTCHA
- Solera Workday Sign In for other reqs if `NAUKRI_WORKDAY_PASSWORD` does not match the tenant account

## Artifacts
`/opt/cursor/artifacts/hitechcity-daily.json`, `hitechcity-careers.json`, `guest-ats-probe.json`
