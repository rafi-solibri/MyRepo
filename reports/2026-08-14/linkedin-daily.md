# Daily Easy Apply — 2026-08-14 (post-fix re-run)

Mohammed Abdul Rafi Ahmed — Easy Apply batch on merged `main` (`8e4652a` + this run’s helper patch).

Automation: https://cursor.com/automations/beb6ef8e-908f-11f1-ba66-0e7d0216e441
Agent: https://cursor.com/agents/bc-b73ef711-4905-4310-af7f-19e7548cf4d6

## Totals

- **Submitted (Easy Apply):** 10 (confirmed `Application submitted`; not invented)
- **Submitted (External ATS):** 0 (stopped — CAPTCHA/checkpoint before external pass)
- **Blocked:** 5 Easy Apply + later `captcha_checkpoint` (auto-login exit 6)
- **Skipped events:** 107 Easy Apply (already applied / Java title / Databricks / SAP / HTTP 999 searches)
- **Resume:** `resumes/Rafi_Resume.docx`

## What ran

1. `git fetch/checkout/pull origin main` then preflight + `launch-chrome-cdp.sh`
2. SQLite `li_at` was present; live probe was `/uas/login`. Password auto-login succeeded (`/feed/`)
3. Easy Apply helper ran ~28 min, 10 submits, then crashed on unguarded `Page.reload` (`ERR_ABORTED` / detached frame)
4. Helper patched in this session (reload guard, HTTP 999 5x retry, BArch/Snowflake/Kerala skips)
5. Resume hit **CAPTCHA/checkpoint** — owner-only; did not invent further applies

## Submitted (Easy Apply)

| Job ID | Role | Location | Notes |
| --- | --- | --- | --- |
| 4453512847 | Solutions Architect - Microsoft Fabric | Hyderabad, Telangana, India | |
| 4454396009 | Solutions Architect - Microsoft Fabric | Hyderabad, Telangana, India | |
| 4453520647 | Solutions Architect - Microsoft Fabric | Hyderabad, Telangana, India | |
| 4450879299 | Solutions Architect - Microsoft Fabric | India (promoted) | |
| 4443883020 | Solutions Architect - Microsoft Fabric | India (promoted) | |
| 4453509656 | Engineering Manager | Hyderabad, Telangana, India | |
| 4450896338 | Interior Architect | Hyderabad, Telangana, India | **false-apply** (BArch) — filter patched |
| 4450815218 | Solutions Architect - Microsoft Fabric | India (promoted) | |
| 4450481862 | Solutions Architect - Microsoft Fabric | India (promoted) | |
| 4453520148 | Snowflake Solutions Architect | Kerala, India | **false-apply** (data/Kerala) — filter patched |

## Blocked (Easy Apply)

- `4454034736` Solutions Architect - Microsoft Fabric — Easy Apply modal did not open
- `4453500167` Engineering Manager — Easy Apply modal did not open
- `4438356022` Senior .NET Engineer — Easy Apply modal did not open
- `4453522530` Interior Architect — exceeded Easy Apply steps
- `4452940611` Snowflake Solutions Architect — Easy Apply time-cap (modal lost)

## Stopped

- Portal **security challenge / CAPTCHA** after the crash (`auto_login.py` exit 6; Google SSO click failed)
- Owner: headed login for this portal, complete checkpoint, refresh `.portal-sessions`, Save snapshot
- Do not wait on this agent to finish remaining 24h/7d/14d inventory

## Code fixes this run (branch pushed)

- Guard empty-search `Page.reload` / card-count so a detached frame skips that search instead of aborting the batch
- Retry HTTP 999/429 search navigation 5 times with longer backoff
- Skip Interior/Landscape Architect, Snowflake architect titles, Kerala as a non-Hyd city
- Login-wall write path no longer clobbers a successful same-day `apply-report.json`

Filter tests: `python3 tools/*/test_filters.py` OK.

## Artifacts

- `/opt/cursor/artifacts/apply-report.json` (restored from first-run log after resume clobber)
- `/opt/cursor/artifacts/easy-apply.log`
