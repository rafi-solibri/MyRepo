# Hitech City / Knowledge City Daily — paste into Agent instructions

Automation: https://cursor.com/automations/b65968f7-953d-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh hitechcity` so resume + LinkedIn cookies are ready (this flow reuses the LinkedIn CDP profile for career portals + referrals).
Then run `bash scripts/launch-chrome-cdp.sh hitechcity`.
Use helper: `python3 tools/hitechcity/daily_apply.py`
Company campus list: `tools/hitechcity/companies.json` (Knowledge City, Knowledge Park, Mindspace Madhapur / Raheja, The V, Cyber Pearl, DLF Cyber City, Divyasree Orion — premium Grade-A buildings). The helper **discovers** additional software tenants into this list before applying (seed employer list + LinkedIn *company-name* slug resolve — not campus-name LinkedIn searches).

Apply to senior .NET / architect / tech-lead / EM roles for Mohammed Abdul Rafi Ahmed at companies in these Madhapur / HITEC City campuses. Maximize BOTH application volume and referral outreach.

**PRIMARY:** official company career portals + LinkedIn company-targeted applies/referrals.
**ALSO REQUIRED (campus allowlist):** browse Naukri, Foundit, Cutshort, Instahyre, and Indeed for the same campus-company set (capped; do not invent applies). Generic Hyd employers outside the campus tenant list stay skipped.

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
ONLY target companies listed in `tools/hitechcity/companies.json` after the discovery step (or clear tenants of the campuses named there).
Priority campuses:
1. Sattva Knowledge City / Knowledge Park (incl. Octave)
2. Mindspace Madhapur (Raheja Mindspace)
3. The V IT Park (Ascendas), Cyber Pearl
4. Peer Grade-A Madhapur / HITEC buildings on the list (DLF Cyber City, Divyasree Orion) when the company is a known premium tenant

Discovery (required each run): `discover_tenants` merges seed + LinkedIn company-search hits into `companies.json` before applies. Never wipe curated Priority-1 rows.

Do NOT apply to random Hyderabad employers outside this campus tenant set. Job boards must use `HITECHCITY_COMPANY_ALLOWLIST` and skip `hitechcity_campus_allowlist` misses.

## Location filter (HARD)
ONLY apply if Hyderabad / Greater Hyderabad / Telangana / Madhapur / HITEC / Gachibowli / Raidurg / Knowledge City OR Fully Remote / WFH / India Remote.
Judge location from the TOP CARD / workplace pills / job location field — never the full page body.

## Apply bias (CRITICAL — volume)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Director .NET/cloud roles at campus companies.
- When uncertain between skip and apply → APPLY (then state expected 65 LPA on forms).
- Aim for a solid daily batch across career portals + LinkedIn (helpers default ~35 LinkedIn applies + career-portal attempts). Do not invent applies; confirm Application submitted / ATS confirmation.

## Apply order (CRITICAL)
1. Run `python3 tools/hitechcity/daily_apply.py` which executes:
   0. Discovery → refresh `companies.json` (+ `hitechcity-discovery.json`)
   1. LinkedIn company applies + referrals (PRIMARY)
   2. Official career portals from `careersUrls` (PRIMARY)
   3. Board browse with campus allowlist: Naukri → Foundit → Cutshort → Instahyre → Indeed (`hitechcity-boards.json`)
2. Or stepwise:
   - `python3 tools/hitechcity/discover_tenants.py`
   - `python3 tools/hitechcity/linkedin_target_apply.py`
   - `python3 tools/hitechcity/careers_apply.py`
   - `python3 tools/hitechcity/board_campus_apply.py`
3. LinkedIn: company-targeted searches on each campus **employer** in `companies.json` (never search campus strings like "Knowledge City" / "Raheja" — discover tenants via seeds + employer-name lookup, then search that company). Keywords: Engineering Manager, Technical Lead, Staff/Principal/Lead Software Engineer, Software Development Manager, Solution/Technical Architect, Principal .NET, Azure/.NET — not architect-only.
4. Easy Apply AND company-website / ATS redirects — both required paths
5. After a successful apply, try referral: message the job poster (poster-specific Message) OR send a short LinkedIn connection note to a Hyd engineer/recruiter/EM at that company asking for a referral / 15–20 min screen
6. For each company: also open official careers URL from companies.json, find Hyd/India qualifying roles, COMPLETE Greenhouse / Lever / Workday / SmartRecruiters / SuccessFactors / company ATS when guest/logged apply is possible (skip US-only cards and SSO passport walls quickly)
7. Boards: each portal gets its own preflight + CDP launch + allowlist; keep per-board caps modest (defaults ~6–12). **Cutshort/Indeed are login-probed first** (`chrome_session.js check`) — skip immediately on `*_login_required` so the phase is not burned. Other board login walls → log blocked, continue.
8. External ATS: default wall/attempt caps are tight (`HITECHCITY_MAX_EXT_WALLS=1`, `HITECHCITY_MAX_EXT_ATTEMPTS=2`, `HITECHCITY_EXT_ATS_TIME_CAP_S=45`) so Phenom/guest walls fail fast and more companies are attempted.
8. Cap stuck ATS/CAPTCHA/OTP at ~3–4 minutes — log blocked, continue. Do **not** require a paid captcha-solver key. Cloud headless cannot click hCaptcha; the free path is owner-headed `bash scripts/home-headed-careers-apply.sh` (helper fills, owner clicks). Optional `CAPSOLVER_API_KEY` only if the owner already set it.
9. Skip already Applied; expand inventory to 14-day window when thin

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
Write `/opt/cursor/artifacts/hitechcity-daily.json` (+ discovery/careers/linkedin/boards sub-reports). Include submitted (company, role, job id/URL, location, Easy Apply vs career ATS vs board), referrals sent, skipped, blocked, discovery added. Totals. Call out campus names when known.

## Auto-fix & push (MANDATORY)
If you hit a code-fixable blocker (company list drift, career scraper, LinkedIn company filter, ATS filler, CDP/preflight), fix under tools/hitechcity or scripts/, append via `bash scripts/append-issue-fix.sh <portal> "issue" "fix"` (writes `automation-prompts/issues/<portal>.md` only — never the shared ISSUES file), commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. That merge helper then same-day re-runs this Hitech City job with the fix (`scripts/rerun-daily-after-fix.sh`) — do not wait for tomorrow's cron. Follow automation-prompts/AUTO_FIX.md. Do not invent applies. Owner-only: login walls, CAPTCHA/OTP, Automations UI paste for ONE_TIME_LOADERS.
```
