# Indeed Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441

Prefer the short loader in [ONE_TIME_LOADERS.md](ONE_TIME_LOADERS.md) (reads this file each run).  
If you paste the full block instead, copy everything inside the fence below and Save.

```text
FIRST: run `node tools/indeed/preflight.js` (WARP SOCKS + Chrome probe + UC Turnstile clear; honors `INDEED_HTTP_PROXY`). Preflight auto-applies `tools/indeed/filelock_patch.py`, multi-strategy Turnstile clicks, and WARP IP rotate. If it still exits 5, stop and report — do not invent applies.
Prefer: `node tools/indeed/daily_apply.js` (wraps preflight + `uc_daily_apply.py`). **Indeed is home-first:** on home Wi‑Fi use `bash scripts/indeed-home-daily.sh` (18:40 IST task). Cloud is best-effort only (CF + session). Optional cloud residential: env secret `INDEED_HTTP_PROXY`.
Then run `bash scripts/preflight-portal-run.sh indeed`. Verify `node tools/indeed/resume.js`.
Then run `bash scripts/launch-chrome-cdp.sh indeed` only if using plain Chrome CDP (Easy Apply on cloud should use UC, not CDP).
Chrome CDP profile: /home/ubuntu/chrome-indeed-profile (synced from Desktop Default).

Daily Indeed (in.indeed.com) apply for Mohammed Abdul Rafi Ahmed.

## Resume (HARD)
Upload **Rafi_Resume.docx** on Easy Apply and every company ATS. Bootstrap paths: /workspace/resumes/Rafi_Resume.docx, /home/ubuntu/Documents/Rafi_Resume.docx. Never invent stubs.
Before each apply, `tools/resume_tailor.py` builds a **JD-tailored** `Rafi_Resume.docx` (headline/summary/skills reorder from the real profile only — never invent stack). Easy Apply + company ATS upload that file (`RESUME_UPLOAD_PATH` / active resume). Disable with `RESUME_TAILOR=0` or `INDEED_TAILOR_RESUME=0`.

## Profile
SA / Technical Architect / Tech Lead / EM / Principal .NET | Hyd + Remote/WFH
Current 52 LPA | Expected 65 LPA | Immediate | +91 8790251698 | rafi.success@gmail.com

## Scope / blockers
- Primary https://in.indeed.com — logged-in session required.
- Cloudflare "Additional Verification Required" / 403 / Request Blocked on cloud: preflight must run WARP SOCKS + SeleniumBase UC Turnstile clear (filelock singleton + retry/handle/blind + WARP rotate). Only stop/report after that exits 5. Do not invent applies.
  Remaining fallbacks (see automation-prompts/INDEED_CLOUDFLARE.md):
  1) Home Wi‑Fi / private residential worker (`scripts/indeed-home-daily.sh`), OR
  2) Env secret `INDEED_HTTP_PROXY` (true residential) then re-run preflight / daily_apply.
- If login missing but page loads: stop and report Indeed login required — Desktop Chrome Default login + sync-chrome-sessions.sh + Save Snapshot.
- Code-fixable CF/preflight bugs (false exit 5, filelock deadlock, UC helper regressions): fix under tools/indeed or scripts/, append via `bash scripts/append-issue-fix.sh <portal> "issue" "fix"`, commit + push + ready PR + `bash scripts/auto-merge-fix-pr.sh` (AUTO_FIX.md), which same-day re-runs this Indeed job.

## Apply bias (CRITICAL)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET/cloud.
- When uncertain → APPLY. Title-first skips only. Do not invent applies.
- Keep going while inventory remains — defaults are **INDEED_MAX_APPLIES=40** / **INDEED_MAX_SEEN=120** (do not soft-stop at ~8).
- Employer SmartApply questions: fill years-with-stack, current employer, LinkedIn URL, education, privacy Agree once (no double-toggle).

## Apply paths
- Prefer Indeed Easy Apply through confirmation via `python3 tools/indeed/uc_daily_apply.py` (cloud WARP+UC path).
- "Apply on company site" / external ATS: FOLLOW and COMPLETE with Rafi_Resume.docx. Do not skip.
- One job at a time; ~3–4 min CAPTCHA cap; continue.

## Location HARD
Hyd/Telangana OR Remote/WFH/India Remote only.

## Filters
Prefer .NET/C# evidence. Skip Java/Node/Python-**mandatory**-only, QA/junior, Salesforce/ServiceNow/SAP-primary titles.
Skip listed max only if clearly under **35 LPA** (forms always 65 expected).
Do NOT skip because JD casually mentions Salesforce/Java/data as adjacent tech.

## Report
Submitted (Easy Apply vs ATS), rejected, skipped, blocked. No invented applies.
When running via home cron (`scripts/indeed-home-daily.sh`), write JSON to
`/opt/cursor/artifacts/indeed-daily-run.json` or `./artifacts/indeed-daily-run.json`
with counts: applied, external, rejected, blocked, skipped, seen — then
`node tools/indeed/daily_run_report.js write --in <file> --source home-local --out <file>`
so the 11 AM Notification Job can include Indeed in the daily mail.

## Auto-fix & push (MANDATORY)
If you hit a code-fixable blocker (preflight false exit 5, filelock/UC Turnstile helper, daily_run_report, publish/fetch scripts, Easy Apply helper), fix durable helpers under tools/indeed or scripts/, append via `bash scripts/append-issue-fix.sh <portal> "issue" "fix"`, commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. That merge helper then same-day re-runs this Indeed job with the fix (`scripts/rerun-daily-after-fix.sh`) — do not wait for tomorrow's cron. Follow automation-prompts/AUTO_FIX.md. Do not invent applies.
Hard residual after WARP+UC multi-strategy + IP rotate still exits 5: report home worker / residential INDEED_HTTP_PROXY (not invent applies).
```
