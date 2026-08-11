# Hitech City / Knowledge City Daily — paste into Agent instructions

Automation: https://cursor.com/automations/b65968f7-953d-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh hitechcity` so resume + LinkedIn cookies are ready (this flow reuses the LinkedIn CDP profile for career portals + referrals).
Then run `bash scripts/launch-chrome-cdp.sh hitechcity`.
Use helper: `python3 tools/hitechcity/daily_apply.py`
Company campus list: `tools/hitechcity/companies.json` (Knowledge City, Knowledge Park, Mindspace Madhapur, The V, Cyber Pearl, DLF Cyber City, Divyasree Orion — premium Grade-A buildings only).

Apply to senior .NET / architect / tech-lead / EM roles for Mohammed Abdul Rafi Ahmed at companies in these Madhapur / HITEC City campuses. Maximize BOTH application volume and referral outreach. Prefer company career portals + LinkedIn company-targeted applies over generic Naukri/Indeed/Foundit browsing (those portals have their own daily automations).

## Profile (use exactly)
- Location preference: Hyderabad, Telangana, India — especially Madhapur / HITEC City / Knowledge City / Knowledge Park / Gachibowli / Raidurg
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
- External ATS / career portals: always `set_input_files` with the canonical docx path.

## Campus / company scope (HARD)
ONLY target companies listed in `tools/hitechcity/companies.json` (or clear tenants of the campuses named there).
Priority campuses:
1. Sattva Knowledge City / Knowledge Park (incl. Octave)
2. Mindspace Madhapur (Raheja Mindspace)
3. The V IT Park (Ascendas), Cyber Pearl
4. Peer Grade-A Madhapur / HITEC buildings on the list (DLF Cyber City, Divyasree Orion) when the company is a known premium tenant

Do NOT spend the run on generic city-wide portal scraping for random Hyderabad employers outside this campus set. Job boards are secondary discovery only when they surface these campus companies’ roles.

## Location filter (HARD)
ONLY apply if Hyderabad / Greater Hyderabad / Telangana / Madhapur / HITEC / Gachibowli / Raidurg / Knowledge City OR Fully Remote / WFH / India Remote.
Judge location from the TOP CARD / workplace pills / job location field — never the full page body.

## Apply bias (CRITICAL — volume)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Director .NET/cloud roles at campus companies.
- When uncertain between skip and apply → APPLY (then state expected 65 LPA on forms).
- Aim for a solid daily batch across career portals + LinkedIn (helpers default ~35 LinkedIn applies + career-portal attempts). Do not invent applies; confirm Application submitted / ATS confirmation.

## Apply order (CRITICAL — LinkedIn company target + career portals)
1. Run `python3 tools/hitechcity/daily_apply.py` (LinkedIn company applies + referrals → career portals)
2. Or stepwise:
   - `python3 tools/hitechcity/linkedin_target_apply.py`
   - `python3 tools/hitechcity/careers_apply.py`
3. LinkedIn: company-targeted searches (Solution Architect, Technical Architect, Software Architect, Technical Lead, Engineering Manager, Principal .NET, Azure/Cloud Architect) restricted to campus companies in companies.json
4. Easy Apply AND company-website / ATS redirects — both required paths
5. After a successful apply, try referral: message the job poster (poster-specific Message) OR send a short LinkedIn connection note to a Hyd engineer/recruiter/EM at that company asking for a referral / 15–20 min screen
6. For each company: also open official careers URL from companies.json, find Hyd/India qualifying roles, COMPLETE Greenhouse / Lever / Workday / SmartRecruiters / SuccessFactors / company ATS when guest/logged apply is possible (skip US-only cards and SSO passport walls quickly)
7. Cap stuck ATS/CAPTCHA/OTP at ~3–4 minutes — log blocked, continue
8. Skip already Applied; expand inventory to 14-day window when thin

## Skip rules (TITLE-FIRST — do not over-filter)
Skip ONLY when the TITLE (or clear mandatory JD language) is wrong:
- Wrong-stack TITLE: Salesforce, ServiceNow, SAP/D365-primary, Guidewire, PEGA, Coupa, Revit/BArch, Hubspot, M365-only, GIS/Esri-primary, QA/SDET/Quality Engineering, BPO, pure AI/data title without .NET on the title
- Wrong-city TITLE/location pills: non-Hyd and not Remote/WFH
- Junior / intern / fresher titles
- JD says Java/Python/Node/Salesforce is **mandatory/required/only** (not a casual mention)
- Listed max CTC clearly under **35 LPA** (35–55 bands are OK — always state 65 expected)
- Company clearly outside the campus tenant list

DO NOT skip because the JD casually mentions Salesforce, SAP, Java, Data Engineer, or other stacks as adjacent teams/tools when the role itself is .NET / architect / lead / EM. Title wins over incidental JD text.

## Form mechanics
- ONE job at a time; close messaging overlays before Next/Submit
- India (+91), CTC 52L current / 65L expected, notice 0
- Confirm Application submitted or ATS confirmation before counting success
- If LinkedIn login missing, stop and report LinkedIn login required (career-portal-only partial run is OK if some applies already landed)

## Report
Write `/opt/cursor/artifacts/hitechcity-daily.json` (+ careers/linkedin sub-reports). Include submitted (company, role, job id/URL, location, Easy Apply vs career ATS), referrals sent, skipped, blocked. Totals. Call out campus names when known.

## Auto-fix & push (MANDATORY)
If you hit a code-fixable blocker (company list drift, career scraper, LinkedIn company filter, ATS filler, CDP/preflight), fix under tools/hitechcity or scripts/, append a row to automation-prompts/ISSUES_AND_FIXES.md, commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. Follow automation-prompts/AUTO_FIX.md. Do not invent applies. Owner-only: login walls, CAPTCHA/OTP, Automations UI paste for ONE_TIME_LOADERS.
```
