# Foundit daily — 2026-08-19

## This session (2nd post-fix re-run, after LinkedIn PR #214)

- `POST_FIX_RERUN=1` on merged `main` (`231b56e` — `fix(linkedin): wait out temp restrictions… (#214)`).
- Preflight + Chrome CDP + `node tools/foundit/daily_apply.js` with `resumes/Rafi_Resume.docx`.
- Logged in: **yes** (MSSOAT + `/seeker/dashboard`; greeting still "Hi, Seeker" — cookie+onApp accepted).
- Applied tab: **511 → 511** (+0). Intentional logged: **0**. No invented applies.
- Skipped: 1189 · Duplicates: 76 (already on Applied tab via `userJobInfo`) · Blocked: 0
- Age window: → **3650d**. Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run calls.

Today's 6 Falcon applies from the earlier post-fix re-run (`bc-c4d93b07`) were skipped as duplicates, including two product-platform false applies that still passed `classifyJob` on main. Filter fix landed in this session (see below).

## Earlier today (1st post-fix re-run `bc-c4d93b07`, 504 → 510)

1. **relq technologies** — Sr .NET Full Stack Developer- India Remote — Falcon 200
2. **embrace software inc** — Senior Developer (.NET) — Falcon 200
3. **Mahindra Satyam** — Technical Architect — Falcon 200
4. **Algoworks Solutions** — Atlassian Solution Architect — Falcon 200 — **false apply** (product-platform SA without .NET on title)
5. **RealPage** — Application Architect (Oracle Subscription Management) — Falcon 200 — **false apply** (Oracle Fusion Cloud ERP product)
6. **GitLab** — Senior Solutions Architect — Falcon 200

Named Foundit Daily (`bc-0da3db32`) then ran 510 → 510 (+0).

## Top skip reasons (this session)

- location not Hyd/remote (567)
- no .NET on title+skills (334)
- no seniority keyword on title (106)
- SAP without .NET (38)
- junior/mid maxExp bands / non-software / infra / pure AI-data

## Code fix this run

Hard-skip `Atlassian` titles without `.NET` on the title (Salesforce/ServiceNow parity) and treat `Oracle Subscription` as Oracle Fusion/ERP so Arch/Lead cannot false-apply those product-platform roles.

## LinkedIn referral drafts

None from this session (0 new applies). Earlier drafts still stand for relq / embrace / Mahindra Satyam.
