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

## Manual step required

Cursor Automations API from this agent is **read-only** (`get-automation` only). Paste each `automation-prompts/0N-*.md` fenced `text` block into the matching automation’s Agent instructions and Save.

**You still must** (not fixable in code alone):
1. Indeed: home Wi‑Fi cron (`scripts/indeed-home-daily.sh`) with push access to `automation-results`
2. Re-paste updated Notification (+ Indeed) loaders after merge
3. Keep General Daily disabled; keep cloud Indeed Daily Off (Cloudflare)
