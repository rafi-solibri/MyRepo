# Indeed Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `node tools/indeed/preflight.js` (HTTP + Chrome probe; honors `INDEED_HTTP_PROXY`). If it exits 5, stop and report that Indeed needs a private worker / residential IP — do not invent applies.
Then run `bash scripts/preflight-portal-run.sh indeed`. Verify `node tools/indeed/resume.js`.
Prefer: `node tools/indeed/daily_apply.js` (wraps preflight). On home Wi‑Fi use `bash scripts/indeed-home-daily.sh`.
Then run `bash scripts/launch-chrome-cdp.sh indeed` if using browser/CDP.
Chrome CDP profile: /home/ubuntu/chrome-indeed-profile (synced from Desktop Default).

**Cloud Indeed Daily automation should stay OFF** (datacenter Cloudflare). Prefer home cron / My Machines private worker.

Daily Indeed (in.indeed.com) apply for Mohammed Abdul Rafi Ahmed.

## Resume (HARD)
Upload **Rafi_Resume.docx** on Easy Apply and every company ATS. Bootstrap paths: /workspace/resumes/Rafi_Resume.docx, /home/ubuntu/Documents/Rafi_Resume.docx. Never invent stubs.

## Profile
SA / Technical Architect / Tech Lead / EM / Principal .NET | Hyd + Remote/WFH
Current 52 LPA | Expected 65 LPA | Immediate | +91 8790251698 | rafi.success@gmail.com

## Scope / blockers
- Primary https://in.indeed.com — logged-in session required.
- If Cloudflare "Additional Verification Required" / 403 / Request Blocked: preflight auto-runs WARP SOCKS + multi-strategy UC Turnstile clear + WARP IP rotate. Only stop/report after that exits 5. Do not invent applies.
  Remaining fix options (see automation-prompts/INDEED_CLOUDFLARE.md):
  1) Run on home Wi‑Fi / private residential worker, OR
  2) Set env secret `INDEED_HTTP_PROXY` then `bash scripts/launch-chrome-cdp.sh indeed`.
- If login missing but page loads: stop and report Indeed login required — Desktop Chrome Default login + sync-chrome-sessions.sh + Save Snapshot.

## Apply bias (CRITICAL)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET/cloud.
- When uncertain → APPLY. Title-first skips only. Do not invent applies.
- Keep going while inventory remains.

## Apply paths
- Prefer Indeed Easy Apply through confirmation.
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
If you hit a code-fixable blocker on a residential/home run (preflight false positive, daily_run_report, publish/fetch scripts, Easy Apply helper), fix durable helpers under tools/indeed or scripts/, append automation-prompts/ISSUES_AND_FIXES.md, commit + push a feature branch, open a draft PR to main. Follow automation-prompts/AUTO_FIX.md. Do not invent applies. Cloudflare on public-cloud IP is NOT code-fixable — report home worker / INDEED_HTTP_PROXY only.
```
