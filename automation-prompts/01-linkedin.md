# LinkedIn Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/beb6ef8e-908f-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh linkedin` so resume + portal cookies are ready and verified.
Then run `bash scripts/launch-chrome-cdp.sh linkedin`.
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
- Canonical: `resumes/Rafi_Resume.docx` → also `/home/ubuntu/resumes/Rafi_Resume.docx` and `/home/ubuntu/Documents/Rafi_Resume.docx` after bootstrap.
- Easy Apply label text: **Rafi_Resume** (upload the docx if LinkedIn has no saved copy).
- Do NOT require Rafi_Resume_Architect.docx. Never invent a stub resume.
- External ATS: always `set_input_files` with the canonical docx path.

## Location filter (HARD)
ONLY apply if Hyderabad / Greater Hyderabad / Telangana OR Fully Remote / WFH / India Remote.
Judge location from the TOP CARD / workplace pills only — never the full page body (profile chrome can contain "Hyderabad" and false-allow Bengaluru roles).

## Search / apply order
1. Latest / Most recent first
2. Hyderabad then Remote India
3. Titles: Solution Architect, Technical Architect, Technical Lead, Engineering Manager, Principal/Staff .NET
4. Skip already Applied
5. Keep going while inventory remains (~20–40 qualifying if available)
6. Retry flaky job-card clicks (scroll into view + retry) before skipping

## Apply paths (CRITICAL — not Easy Apply only)
- Prefer Easy Apply through Application submitted
- If Apply / company website / Workday / Greenhouse / Lever / SmartRecruiters / SuccessFactors / BambooHR / Hibob: FOLLOW and COMPLETE. Do not skip externals.
- One job at a time; ~3–4 min cap on stuck ATS/CAPTCHA/OTP — log blocked, continue
- Greenhouse email OTP: if GMAIL session available in Chrome, read OTP; else block and continue
- After Easy Apply, message the poster (poster-specific Message, not generic typeahead) asking for a 15–20 min screen

## Skip blacklist
Salesforce, ServiceNow, SAP/D365, Guidewire, Splunk, PEGA, Java-mandatory-only, Oracle ERP, Sitecore-only, MEAN, DevOps/SRE-primary (unless strong .NET/platform lead), GCP-presales-only, data-only, niche AI-only (no .NET), Node/Java/Python/Golang-mandatory backends with no .NET, low CTC (listed max ~15–50 LPA), BPO SA, RoR, firmware, MES/ERP-primary, Blockchain, GIS/Esri-primary, Mandarin-required, BizTalk-deep-mandatory, iPaaS-only, Coupa, interior designer, electrical EM, roles no longer accepting, non-Hyderabad non-remote

## Form mechanics
- ONE job at a time; close messaging overlays before Next/Submit
- If job page empty, wait/reload
- India (+91), CTC 52L current / 65L expected, notice 0
- Confirm Application submitted or ATS confirmation before counting success
- If login missing, stop and report LinkedIn login required

## Report
submitted (company, role, job id, location, Easy Apply vs ATS URL), skipped, blocked. Totals.
```
