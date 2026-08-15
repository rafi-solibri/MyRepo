# Hitech City / Knowledge City daily — 2026-08-15 (career portals)

## Status
**Careers pass completed** — 0 new confirmation applies this session. LinkedIn skipped (CAPTCHA/checkpoint). Boards skipped (careers-only).

## Totals
- Career ATS submitted: **0**
- Blocked: **16** (DataDome/reCAPTCHA + Solera Workday login)
- Skipped: **23** (hang-scan hosts, location, wrong-stack, already-applied / no form)
- Scanned companies: **27**

## Applied
None this session. Earlier same-day cloud run already submitted **Solera JR-019000** (Workday). Re-open of that req is now treated as `already_applied` (skip), not a login wall.

## Blockers (do not repeat)
| Issue | Fix landed this run |
| --- | --- |
| Workday Create Account burned 390s on password-rule / empty `/login` | Fail-fast `inputAlert` + standalone `/login`; deterministic 12+ complexity password |
| Careers-only still launched WARP + LinkedIn auto-login | `HITECHCITY_CAREERS_ONLY` skips WARP and LinkedIn login |
| Goldman `higher.gs.com` hung extract and starved remaining ATS | Hang-scan host skip |
| `Frame.evaluate(timeout=)` TypeError emptied every scan | Removed invalid kwarg |
| Hyland/Intel/JPMC `jobCount: 0` before cards rendered | Wait for Workday/iCIMS/Oracle job cards |
| Solera already-applied counted as `ats_login_wall` | `already_applied` skip |

## Owner-only (cannot fix in code)
- LinkedIn `/checkpoint/challenge` — `bash scripts/home-headed-login.sh linkedin` + Save snapshot
- Experian / Blackbaud / Palo Alto DataDome or reCAPTCHA
- Solera Workday Sign In still fails for other reqs if the stored secret does not match the existing tenant account — set a 12+ complexity `NAUKRI_WORKDAY_PASSWORD`

## Artifacts
`/opt/cursor/artifacts/hitechcity-daily.json`, `hitechcity-careers.json`, `hitechcity-careers-run.log`
