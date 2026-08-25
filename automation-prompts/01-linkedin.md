# LinkedIn Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/beb6ef8e-908f-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh linkedin` so resume + portal cookies are ready and verified.
Then run `bash scripts/launch-chrome-cdp.sh linkedin`.
Launch auto-heals LinkedIn login: WARP SOCKS on cloud + `tools/linkedin/auto_login.py` (Continue with Google; optional secrets LINKEDIN_EMAIL/LINKEDIN_PASSWORD) + `scripts/refresh-portal-session-seed.sh` on success. Do not ask the owner to headed-login unless auto-login exits CAPTCHA (6) with no Google session.
Use helpers: `python3 tools/linkedin/linkedin_easy_apply.py` and `python3 tools/linkedin/linkedin_external_apply.py`.
Never use the Default google-chrome profile for CDP — sync copies logins into chrome-cdp-profile.

Apply to LinkedIn jobs for Mohammed Abdul Rafi Ahmed (Rafi Ahmed) until a solid daily batch is done or inventory runs thin. Maximize BOTH application volume and interview callbacks.

## Profile (use exactly)
- Location preference: Hyderabad, Telangana, India
- Phone: +91 8790251698 | Email: rafi.success@gmail.com
- LinkedIn: https://linkedin.com/in/rafi-ahmed-mohammed-abdul-151644ba
- DOB: 16 January 1989 (day=16, month=January/Jan/01, year=1989)
- Notice: Immediate (0 days)
- Current CTC: 5200000 (52 LPA) | Expected CTC: 6500000 (65 LPA) — use these numbers on ALL forms
- Experience: ~15 years; .NET Core, microservices, AWS/Azure, Kafka/RabbitMQ, K8s, Angular/React
- Resume: Rafi_Resume.docx only
- Education: Acharya Nagarjuna University, B.Tech IT — July 2006 to May 2010
- Employer: Nemetschek / Solibri / Spacewell (Principal Analyst)

## Resume (HARD)
- Canonical base: `resumes/Rafi_Resume.docx` → also `/home/ubuntu/resumes/Rafi_Resume.docx` and `/home/ubuntu/Documents/Rafi_Resume.docx` after bootstrap.
- **Per-job tailor (MANDATORY):** before each Easy Apply / external ATS upload, run `tools/resume_tailor.py` (helpers call it automatically) so headline, summary, skills order, and bullets are JD-keyword aligned. Never invent employers, dates, titles, or metrics — only emphasize owned .NET/cloud/leadership experience that matches the JD.
- Upload the tailored copy (still named **Rafi_Resume.docx** / label **Rafi_Resume**). Prefer file-input upload over a stale LinkedIn-saved resume.
- Do NOT require Rafi_Resume_Architect.docx. Never invent a stub resume.
- External ATS: always `set_input_files` with the active tailored path from `tools.resume_paths.resume_upload_path()` (falls back to canonical).
- Disable only for debug: `RESUME_TAILOR=0` / `LINKEDIN_TAILOR_RESUME=0`.

## Location filter (HARD)
ONLY apply if Hyderabad / Greater Hyderabad / Telangana OR Fully Remote / WFH / India Remote.
Judge location from the TOP CARD / workplace pills only — never the full page body (profile chrome can contain "Hyderabad" and false-allow Bengaluru roles).

## Apply bias (CRITICAL — volume)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Director .NET/cloud roles.
- When uncertain between skip and apply → APPLY (then state expected 65 LPA on forms).
- Aim for **40–50+** qualifying Easy Applies when inventory exists. Do not stop at ~20.
- Helpers default MAX_APPLY=50 / MAX_EXTERNAL=25 / scan deeper + 14-day window.
- Do NOT invent applies; confirm Application submitted / ATS confirmation.

## Search / apply order
1. Latest / Most recent first
2. Hyderabad then Remote India
3. Titles: Solution Architect, Technical Architect, Software Architect, Technical Lead, Engineering Manager, Principal/Staff .NET, Azure/Cloud Architect
4. Skip already Applied
5. Keep going while inventory remains (expand to 7d then 14d if thin)
6. Retry flaky job-card clicks (scroll into view + retry) before skipping

## Apply paths (CRITICAL — not Easy Apply only)
- Prefer Easy Apply through Application submitted
- The durable runner **always** runs a **non-Easy-Apply search pass** (`f_AL` off) so company-site / Apply jobs are collected even after Easy Apply volume or a daily Easy Apply limit. Set `LINKEDIN_EASY_APPLY_ONLY=1` only to disable that pass. External helper cap: `LINKEDIN_MAX_EXTERNAL` (default 40).
- If Apply / company website / Workday / Greenhouse / Lever / SmartRecruiters / SuccessFactors / BambooHR / Hibob: FOLLOW and COMPLETE. Do not skip externals.
- Dedup: load prior job IDs from `/opt/cursor/artifacts/linkedin-seen-ids.json` + prior apply reports (plus bootstrap seed). Do not re-apply known IDs.
- One job at a time; ~6.5 min cap on Workday/Greenhouse ATS (LINKEDIN_ATS_TIME_CAP_S=390). CAPTCHA/OTP: log blocked, continue
- Greenhouse / Oracle email OTP: `tools/ats/email_otp.py` reads Gmail (CDP session) or IMAP (`GMAIL_APP_PASSWORD`) and fills the code; only block+continue when mailbox is unavailable
- After Easy Apply, message the poster (poster-specific Message, not generic typeahead) asking for a 15–20 min screen

## Skip rules (TITLE-FIRST — do not over-filter)
Skip ONLY when the TITLE (or clear mandatory JD language) is wrong:
- Wrong-stack TITLE: Salesforce, ServiceNow, SAP/D365-primary, Guidewire, PEGA, Coupa, Revit/BArch, Hubspot, M365-only, GIS/Esri-primary, QA/SDET/Quality Engineering, BPO, pure AI/data title without .NET on the title
- Wrong-city TITLE/location pills: non-Hyd and not Remote/WFH
- Junior / intern / fresher titles
- JD says Java/Python/Node/Salesforce is **mandatory/required/only** (not a casual mention)
- Listed max CTC clearly under **35 LPA** (35–55 bands are OK — always state 65 expected)

DO NOT skip because the JD casually mentions Salesforce, SAP, Java, Data Engineer, presales, or other stacks as adjacent teams/tools when the role itself is .NET / architect / lead / EM. Title wins over incidental JD text.

## Form mechanics
- ONE job at a time; close messaging overlays before Next/Submit
- If job page empty, wait/reload
- India (+91), CTC 52L current / 65L expected, notice 0
- Confirm Application submitted or ATS confirmation before counting success
- If login missing, stop and report LinkedIn login required

## Report
submitted (company, role, job id, location, Easy Apply vs ATS URL), skipped, blocked. Totals. Call out any false-skip suspects.

## Auto-fix & push (MANDATORY)
If you hit a code-fixable blocker (filters, Easy Apply/Greenhouse filler, external ATS helper, CDP/preflight), fix the durable helper under tools/linkedin or scripts/, append via `bash scripts/append-issue-fix.sh <portal> "issue" "fix"` (writes `automation-prompts/issues/<portal>.md` only — never the shared ISSUES file), commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. That merge helper then same-day re-runs this LinkedIn job with the fix (`scripts/rerun-daily-after-fix.sh`) — do not wait for tomorrow's cron. Follow automation-prompts/AUTO_FIX.md. Do not invent applies. Owner-only: login walls, CAPTCHA/OTP.
```
