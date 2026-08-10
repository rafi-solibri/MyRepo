# What changed vs today’s live prompts

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

## Prompt update policy

Cursor Automations API from this agent is **read-only** (`get-automation` only),
so agents cannot paste or save Automation UI instructions. The durable solution is
the one-time loader pattern in [ONE_TIME_LOADERS.md](ONE_TIME_LOADERS.md):
paste each short loader once, then future prompt refinements are delivered by
merging changes to `automation-prompts/*.md` on `main`.

**No recurring manual re-paste is required** after prompt files change, as long as
the matching automation still contains its one-time loader.

Still not fixable from code alone:
1. Keep **cloud Indeed Daily OFF** unless it runs on home/private worker or via proxy
2. Set `RESEND_FROM_EMAIL` for Notification
3. Keep General Daily disabled
