# What changed vs today’s live prompts

## 2026-08-26 — Honest applies + Notification cloud-only + Google 2FA

| Area | Change |
| --- | --- |
| Foundit | Count **applied** only when company ATS reaches `linkedin_easy_apply_ok` / `ats_submitted`. Falcon `APPLY_REDIRECT` alone → `external_ats_incomplete` (not applied). LinkedIn path tries company Apply when no Easy Apply. |
| Notification | Home-local **disabled** for reporting; cloud agents only; always wait/poll Hitech ~11 AM automation; honest ATS-confirmed counts |
| Google auth | Shared `GOOGLE_AUTH.md` + `tools/google_2fa_prompt.py` — `ASK_OWNER_GOOGLE_2FA` in chat for mobile owner |
| Hirist | `tools/hirist/google_login.js` Gmail SSO; wired from `daily_apply.js` |
| LinkedIn | auto_login waits on Google 2FA with chat banner |
| Resume | Unchanged: every run rebuilds `Rafi_Resume.docx` from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx` via `ensure_upload_resume.py`; JD tailor default ON |

## 2026-08-24 — Hirist Daily portal

| Area | Change |
| --- | --- |
| New portal | `tools/hirist/` daily runner (gladiator search + apply-multiple) + `09-hirist.md` |
| Launcher | Hirist added to `scripts/launch-daily-portals.sh` (GHA 9 AM IST) |
| Home | HomeDaily-Hirist task + fetch/publish/notification wiring |
| Owner | Paste ONE_TIME_LOADERS Hirist loader into a new Cursor Automation; `home-headed-login.sh hirist` once |

## Shared corrections (all apply agents)

| Topic | Before (inconsistent) | After |
| --- | --- | --- |
| Expected CTC | 60 LPA on LinkedIn/Foundit/General; 65 on Cutshort | **65 LPA everywhere** |
| Current CTC | 52 LPA where set | **52 LPA** (unchanged) |
| Location | Mostly Hyd + remote | **Hard filter** Hyd / Telangana **or** Remote/WFH |
| Apply path | LinkedIn/Foundit often **skipped** non–Easy/Quick Apply | **Must complete company website / ATS** redirects |
| Volume | Soft / early stop | Keep going while qualifying inventory remains |
| Interview calls | Partial (notes/messages) | Explicit screening-call ask + JD-tailored blurbs |

## Per automation

1. **LinkedIn** — Removed “skip external Apply”; expected CTC 60→65; volume + interview follow-up strengthened.
2. **Foundit** — External Workday/LinkedIn/company sites are now **complete**, not skip; CTC 65.
3. **Cutshort** — Locked expected CTC to **65** (was ~65); added external ATS completion; Hyd/remote hard filter.
4. **General** — Rewritten as **Naukri-first + company ATS** (was vague resume-only / no submits). This addresses Naukri “apply on company website” stopping.
5. **Instahyre / Indeed** — Full prompts aligned to same profile, CTC, location, and external-apply rules (prior prompts not readable from expired runs).
6. **Notification 11 AM** — Lists cloud apply automations + **Indeed home-local** results via `fetch-indeed-home-result.sh` (applied/rejected/blocked/skipped) + external-apply counts + 65 LPA note.

## 2026-08-10 blocker pass

- Naukri STEP 0 resume refresh hardened + auto-run from `daily_apply.js`
- Foundit `filters.js` (title experience bands)
- LinkedIn blacklist for Revit/Hubspot/M365/AI-only/QA
- Instahyre `filters.js` Quality Engineering skip
- Indeed Cloudflare docs + `INDEED_HTTP_PROXY` support in Chrome CDP launch

## 2026-08-10 Indeed daily mail

- Home Indeed cron publishes JSON counts to branch `automation-results`
- Notification Job must fetch home results (not cloud Cloudflare stub) for Indeed

## 2026-08-10 volume / false-skip + full reliability pass

| Area | Fix |
| --- | --- |
| LinkedIn filters | Title-first blacklist (`filters.py`); broader TITLE_OK; MAX_APPLY=50 / MAX_EXTERNAL=25 / 14-day |
| LinkedIn Easy Apply | Greenhouse education/LinkedIn URL/engineers managed/checkbox fill + 3-min time-cap |
| LinkedIn external | Always queue PRIORITY_IDS |
| Naukri | CTC floor 35; arch/lead without card .NET; skip pure AI titles; MAX_APPLIES=60 |
| Foundit | Senior .NET seniority; CTC 35; keep Capgemini 6-9 reject; `daily_apply.js` |
| Cutshort | Free-text questionnaire payload; restored `daily_apply.js`; CTC floor 35 |
| Instahyre | CTC parse in `skipReason`; `daily_apply.js` |
| Indeed | `chrome_probe.js` + proxy-aware preflight; `daily_apply.js` gate; Windows home task installer; cloud automation stay OFF |
| Prompts | Apply-bias + title-first + 40–50+ volume; runners referenced; ENV_READINESS updated |

## 2026-08-11 Hitech City / Knowledge City Daily

New campus-focused automation (same profile/CTC/resume rules as portal dailies):

| Area | Detail |
| --- | --- |
| Automation | `b65968f7-953d-11f1-ba66-0e7d0216e441` (rename Untitled → **Hitech City / Knowledge City Daily**) |
| Prompt | `automation-prompts/08-hitech-city.md` + ONE_TIME_LOADERS entry |
| Company list | `tools/hitechcity/companies.json` — Knowledge City / Knowledge Park / Mindspace Madhapur / The V / Cyber Pearl / peer Grade-A tenants |
| Runner | `python3 tools/hitechcity/daily_apply.py` — **parallel multi-tab careers** (`HITECHCITY_PARALLEL_TABS=10` every cron/daily) first, then LinkedIn company applies + referral notes |
| CDP | `hitechcity` portal alias reuses LinkedIn Chrome profile |
| Notification | `07-notification.md` includes this automation’s totals |

## 2026-08-11 Windows agent worker ABI

- Documented Cursor Windows `better-sqlite3` 127/137 crash (reinstall useless)
- Added `scripts/fix-windows-agent-worker.ps1` + `scripts/setup-wsl-agent-worker.sh`
- Prefer WSL private worker (`job-apply-laptop` / `indeed-home`) until Cursor ships a fixed Win package

## Manual step required

Cursor Automations API from this agent is **read-only** (`get-automation` only). Paste each `automation-prompts/0N-*.md` fenced `text` block into the matching automation’s Agent instructions and Save.

**You still must** (not fixable in code alone):
1. Keep **cloud Indeed Daily OFF**; use home cron / private worker
2. On Windows laptop: start the worker via **WSL** (not native `agent worker start`) until Cursor fixes the package
3. Re-paste **all** updated apply prompts after merge (including **08-hitech-city** loader)
4. Rename Untitled automation → **Hitech City / Knowledge City Daily**
5. Set `RESEND_FROM_EMAIL` for Notification
6. Keep General Daily disabled
