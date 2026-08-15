# Hitech City home daily 2026-08-15

Mohammed Abdul Rafi Ahmed | Expected **65 LPA** / Current **52 LPA** | Hyd + Remote | resume `Rafi_Resume.docx`

Source: **home-local** (Windows residential, `CHROME_CDP_MODE=system`)

## Totals

| Metric | Count |
| --- | ---: |
| Applied (confirmed this run) | 0 |
| Referrals sent | 0 |
| Skipped | 732 |
| Blocked | 32 |
| Careers scanned | Hyland + cascade after Chrome death |
| Discovery added | 0 (69 tenants; LinkedIn discovery disabled — no live `li_at`) |

## Submitted

None confirmed for this Hitech City run. Do not invent applies.

## Campuses / portals

Knowledge City / Knowledge Park / Mindspace Madhapur / Divyasree Orion / DLF Cyber City / Cyber Pearl / The V via `tools/hitechcity/companies.json` (69 tenants).

| Phase | Result |
| --- | --- |
| Discovery | updated 27 / total 69; LinkedIn discovery `disabled` (no login) |
| Careers | 0 applied; Hyland `owner_captcha_unsolved` then Chrome closed; remaining tenants `browser has been closed` |
| LinkedIn + referrals | blocked — CDP `ECONNREFUSED` after Chrome died |
| Boards | Naukri `error` (launch syntax warning + closed page); Foundit `preflight_rc_3`; Cutshort `timeout_900s`; Instahyre ok (0 campus matches); Indeed `indeed_login_required` |

## Blockers (owner)

1. **LinkedIn login** — `bash scripts/home-headed-login.sh linkedin` (or `hitechcity`), then re-run.
2. **Hyland iCIMS hCaptcha** — click captcha in headed Chrome (or set CapSolver/2Captcha key). Helper waits via `ATS_CAPTCHA_WAIT_SEC` / `HOME_LOCAL`.
3. Board logins: Foundit / Indeed / refresh Naukri CDP session as needed.

## Code fixes this run

| PR | Fix |
| --- | --- |
| [#178](https://github.com/rafi-solibri/MyRepo/pull/178) | Fail-fast hCaptcha owner-wait polls (skip cross-origin iframes + 2.5s timeout); `connect_over_cdp` timeout 20s |
| Follow-up | Careers CDP reconnect when Chrome closes mid-scan (shipping after this report) |

## Artifacts

- `artifacts/hitechcity-daily.json`, `hitechcity-careers.json`, `hitechcity-linkedin.json`, `hitechcity-boards.json`, `hitechcity-discovery.json`
- Home mail JSON: `artifacts/hitechcity-daily-run.json` → `automation-results/hitechcity/2026-08-15.json`
