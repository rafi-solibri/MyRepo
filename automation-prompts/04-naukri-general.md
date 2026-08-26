# Naukri Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
General Daily 9 AM (`30e2c023-9067-11f1-ba66-0e7d0216e441`) is duplicate/noisy; disable it in the Automations UI.

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh naukri`. Verify `node tools/naukri/resume_and_filters.js`.
Then run `bash scripts/launch-chrome-cdp.sh naukri`.
Chrome CDP profile: /home/ubuntu/.naukri-chrome-profile (synced from Desktop Default; Default rejects DevTools). Port 9222.
Title skips: use job title / job-panel text only — never full document.body (sidebar "Software & QA" false-skips SA roles). Prefer `shouldSkipTitle` / `shouldSkipTitleFromDetail` from resume_and_filters.js.

Daily Naukri + company-ATS apply for Mohammed Abdul Rafi Ahmed. Hyd + Remote/WFH. Expected CTC 65 LPA. Maximize real applies.

## Resume (HARD)
- **Owner master (source of truth):** `resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx`. Drop a new master here to update every portal.
- **Upload copy:** bootstrap / `tools/ensure_upload_resume.py` ALWAYS rebuilds `resumes/Rafi_Resume.docx` from that master (font-stripped for Naukri’s 2MB cap). Never reuse a stale committed `Rafi_Resume.docx`.
- Upload **Rafi_Resume.docx** on every company ATS. Never invent a stub. Do not require Rafi_Resume_Architect.docx.
- **Per-job JD tailor (default on):** `daily_apply.js` runs `tailor_resume.py` before each apply — rewrites headline + summary to emphasize JD-matched skills that already exist on the CV (never invents stacks/employers). Quick Apply syncs the tailored file to the Naukri profile first; company ATS/Workday upload the tailored path. Disable with `NAUKRI_TAILOR_RESUME=0`. Profile is restored to the canonical CV at end of run.

## STEP 0 — Naukri profile resume refresh (HARD — do before any job applies)
Goal: recruiters see an updated resume / “Updated today” every morning so the profile looks actively looking and ranks better for interview calls.

1. Confirm Naukri login (Hi / profile name). If login/OTP: use Gmail in same Chrome profile; if impossible, stop and report.
2. Prefer one command that does STEP 0 + applies: `node tools/naukri/daily_apply.js` (it now runs `update_profile_resume.js` first).
   Or run alone: `node tools/naukri/update_profile_resume.js`
   - Must use resume-specific inputs `#attachCV` / `#lazyAttachCV` (never a random page file input).
   - Soft-touch Resume Headline (edit → Save) so last-updated advances if file upload alone does not.
   - Retries up to 3 times until `verify.todayHit` / `profileUpdated: true`.
3. Verify success: `/opt/cursor/artifacts/naukri-profile-resume.json` has `profileUpdated: true` and updateOn / “Updated today”.
4. If profile resume update still fails after retries, report it clearly (`reason: updated_today_unconfirmed`), then CONTINUE with job applies (do not abort the whole day unless login is missing).
5. Do this EVERY daily run even if the file content is unchanged — re-upload is the point (freshness signal).
6. Hirist “On hirist” login walls: SKIP (do not count as hard blocked). Optional: Desktop login to Hirist + re-seed session later.

## Profile
Phone +91 8790251698 | rafi.success@gmail.com | Current 52 LPA | Expected 65 LPA | Immediate
Stack: .NET Core/C#, AWS/Azure, Kafka/RabbitMQ, K8s, React/Angular | 15+ years
Preferred resume headline (keep / restore if wiped):
Solutions Architect & Technical Lead - 15+ Yrs - .NET Core, Microservices, AWS&Azure, Kafka&RabbitMQ

## Apply bias (CRITICAL — volume)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Director roles.
- Architect/Lead/EM titles may proceed even if the card snippet does not show “.NET” (JD often buries it). Still skip Coupa/Pega/Salesforce/SAP-primary titles via `shouldSkipTitle`.
- Skip listed max CTC only if clearly under **35 LPA** (Incedo/Capgemini 30–40 bands that were wrongly hard-skipped should now apply when ≥35; always state 65 expected).
- Prefer `node tools/naukri/daily_apply.js` (MAX_APPLIES default 60). Auto early-expand: after freshest age, if applied &lt; `NAUKRI_EARLY_EXPAND_BELOW` (default 3) continue remaining primary ages immediately; if still &lt; `NAUKRI_EXPAND_BELOW` (default 8) expand ages 15/30/60 and run extra .NET/Azure queries. Keep cyber/QA/Salesforce title skips.
- When uncertain → APPLY. Do not invent applies.

## Primary board (after STEP 0)
1. Newest 1d→3d→7d (then 15/30/60 + extra queries if thin). Filters Hyd/Secunderabad + Remote/WFH. Exp ~10–20.
2. Queries: Solution Architect .NET, Technical Architect .NET, .NET Technical Lead, Engineering Manager .NET, Principal Engineer .NET, Azure Architect .NET, Software Architect .NET

## TopTier UI
- Cards are div.cursor-pointer. Quick Apply opens a popup.
- Success = detail CTA shows Applied. Sidebar "Applied (N)" is a FILTER CHIP — never per-job status.
- Use tools/naukri/resume_and_filters.js for Coupa/Pega/SAP/Salesforce skips (Intern must not match Internet).

## Apply paths (CRITICAL)
- Naukri Quick Apply when it submits on Naukri.
- If "Go to company site" / "On company site" / "Apply on company site" / Workday / Greenhouse / Lever / SmartRecruiters / SuccessFactors / etc.: OPEN and COMPLETE with Rafi_Resume.docx + 52/65/immediate/Hyd. Prefer **Go to company site** when Apply-on is disabled (“Apply attempted”). Log each redirect URL + outcome.
- Cap CAPTCHA/login walls ~3–4 min → blocked → continue.
- After apply, attempt contact recruiter / chat with 15–20 min screen ask.

## Location HARD
Hyd/Telangana OR Remote/WFH only.

## Report
1) Profile resume refresh: ok/fail + updateOn text + resume filename shown
2) Every job submit: company, role, id/URL, location, Naukri vs ATS path, resume file used
Counts: profileUpdated / applied / external / blocked / skipped


## Google / Gmail auth
Follow `automation-prompts/GOOGLE_AUTH.md` every run: prefer Gmail SSO where offered; autofill email OTP via `tools/ats/email_otp.py`; on Google 2FA print `ASK_OWNER_GOOGLE_2FA` in chat and wait for the owner mobile code. Complete company ATS to submitted — never count redirect-only as applied.
## Auto-fix & push (MANDATORY)
If you hit a code-fixable blocker (update_profile_resume.js, daily_apply.js, resume_and_filters.js, Hirist skip), fix durable helpers under tools/naukri or scripts/, append via `bash scripts/append-issue-fix.sh <portal> "issue" "fix"`, commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. That merge helper then same-day re-runs this Naukri job with the fix (`scripts/rerun-daily-after-fix.sh`) — do not wait for tomorrow's cron. Follow automation-prompts/AUTO_FIX.md. Do not invent applies. Owner-only: Naukri login/OTP, snapshot cookies, Hirist login (optional).
```
