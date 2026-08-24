# Hitech City / Knowledge City Daily — paste into Agent instructions

Automation: https://cursor.com/automations/b65968f7-953d-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh hitechcity` so resume + LinkedIn cookies are ready (this flow reuses the LinkedIn CDP profile for career portals + referrals).
Then run `bash scripts/launch-chrome-cdp.sh hitechcity`.
Use helper: `python3 tools/hitechcity/daily_apply.py`
Company campus list: `tools/hitechcity/companies.json` (Knowledge City, Knowledge Park, Mindspace Madhapur / Raheja, The V, Cyber Pearl, DLF Cyber City, Divyasree Orion — premium Grade-A buildings). The helper **discovers** additional software tenants into this list before applying (seed employer list + LinkedIn *company-name* slug resolve — not campus-name LinkedIn searches).

Apply to senior .NET / architect / tech-lead / EM roles for Mohammed Abdul Rafi Ahmed at companies in these Madhapur / HITEC City campuses. Maximize BOTH application volume and referral outreach. Target ~50 applications/day.

**PRIMARY:** official company career portals in **parallel multi-tab** (default `HITECHCITY_PARALLEL_TABS=10` on every cron/daily/`daily_apply.py` run) + LinkedIn company-targeted applies/referrals.
**ALSO REQUIRED (campus allowlist):** browse Naukri, Foundit, Cutshort, Instahyre, and Indeed for the same campus-company set (capped; do not invent applies). Generic Hyd employers outside the campus tenant list stay skipped.
Owner only solves captchas: every daily run **re-focuses the captcha / ASK_OWNER tab** (`focus_page_for_owner` + CDP activate, every ~2s via `ATS_OWNER_FOCUS_EVERY_SEC`) so parallel workers cannot leave you on the wrong tab. Workers keep filling/submitting on other company tabs. Do not set `HITECHCITY_PARALLEL_TABS=1` unless debugging a single portal.

## Profile (use exactly)
- Location preference: Hyderabad, Telangana, India — especially Madhapur / HITEC City / Knowledge City / Knowledge Park / Gachibowli / Raidurg
- Phone: +91 8790251698 | Email: [APPLY_EMAIL]
- LinkedIn: https://linkedin.com/in/rafi-ahmed-mohammed-abdul-151644ba
- DOB: 16 January 1989 (day=16, month=January/Jan/01, year=1989)
- Notice: Immediate (0 days)
- Current CTC: 5200000 (52 LPA) | Expected CTC: 6000000 (60 LPA) — use these numbers on ALL forms
- Experience: ~15 years; .NET Core, microservices, AWS/Azure, Kafka/RabbitMQ, K8s, Angular/React
- Resume: Rafi_Resume.docx only — **per-JD tailored** before each ATS/Easy Apply upload (`RESUME_TAILOR=1` default via `tools/resume_tailor.py`). Filename stays `Rafi_Resume.docx`; never invent skills/employers.
- Education: Acharya Nagarjuna University, B.Tech IT — July 2006 to May 2010
- Employer: Nemetschek / Solibri / Spacewell (Principal Analyst)

## Resume (HARD)
- Canonical: `resumes/Rafi_Resume.docx` → also `/home/ubuntu/resumes/Rafi_Resume.docx` and `/home/ubuntu/Documents/Rafi_Resume.docx` after bootstrap.
- Easy Apply label text: **Rafi_Resume** (upload the docx if LinkedIn has no saved copy).
- Do NOT require Rafi_Resume_Architect.docx. Never invent a stub resume.
- External ATS / career portals: always `set_input_files` with a **JD-tailored** `Rafi_Resume.docx` (truthful rewrite of headline/summary/skill order from the canonical file via `tools/resume_tailor.py`). Disable with `RESUME_TAILOR=0`.

## Campus / company scope (HARD)
ONLY target companies listed in `tools/hitechcity/companies.json` after the discovery step (or clear tenants of the campuses named there).
Priority campuses:
1. Sattva Knowledge City / Knowledge Park (incl. Octave)
2. Mindspace Madhapur (Raheja Mindspace)
3. The V IT Park (Ascendas), Cyber Pearl
4. Peer Grade-A Madhapur / HITEC buildings on the list (DLF Cyber City, Divyasree Orion) when the company is a known premium tenant

Discovery (required each run): `discover_tenants` merges the full Madhapur/HITEC campus tenant catalog (Raheja Mindspace, Knowledge City, Knowledge Park, The V, Cyber Pearl, DLF, Orion) plus live Mindspace REIT / Cityinfo directory scrapes into `companies.json` before applies. Never wipe curated Priority-1 rows. LinkedIn company-name slug search stays off by default.

Do NOT apply to random Hyderabad employers outside this campus tenant set. Job boards must use `HITECHCITY_COMPANY_ALLOWLIST` and skip `hitechcity_campus_allowlist` misses.

## Location filter (HARD)
ONLY apply if Hyderabad / Greater Hyderabad / Telangana / Madhapur / HITEC / Gachibowli / Raidurg / Knowledge City OR Fully Remote / WFH / India Remote.
Judge location from the TOP CARD / workplace pills / job location field — never the full page body.

## Apply bias (CRITICAL — volume + never abandon matching jobs)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Director .NET/cloud roles at campus companies.
- When uncertain between skip and apply → APPLY (then state expected 60 LPA on forms).
- **NEVER skip a criteria-matching job without applying.** Auto-fill all fields (including Source / How did you hear, iCIMS Email + I accept + Next). If a field/login/captcha still blocks submit, print `ASK_OWNER` and wait (headed/`HOME_LOCAL`) for the owner to finish — do not mark incomplete and move on.
- Soft `external_incomplete_or_timeout` must NOT trip per-company attempt caps that skip remaining matching roles.
- Aim for a solid daily batch across career portals + LinkedIn. Do not invent applies; confirm Application submitted / ATS confirmation.

## Apply order (CRITICAL)
1. Run `python3 tools/hitechcity/daily_apply.py` (every cron / home / headed run) which executes:
   0. Discovery → refresh `companies.json` (+ `hitechcity-discovery.json`)
   1. Official career portals from `careersUrls` in **PARALLEL** (PRIMARY) — `HITECHCITY_PARALLEL_TABS=10` by default via `careers_parallel.py` (ProcessPool; one CDP tab per worker). Log line: `CAREERS PARALLEL start tabs=10`.
   2. LinkedIn company applies + referrals (PRIMARY)
   3. Board browse with campus allowlist: Naukri → Foundit → Cutshort → Instahyre → Indeed (`hitechcity-boards.json`)
2. Or stepwise:
   - `python3 tools/hitechcity/discover_tenants.py`
   - `python3 tools/hitechcity/careers_apply.py` (same parallel default when not already a worker)
   - `python3 tools/hitechcity/linkedin_target_apply.py`
   - `python3 tools/hitechcity/board_campus_apply.py`
3. Volume defaults every `daily_apply` run (override only when debugging): `HITECHCITY_PARALLEL_TABS=10`, `HITECHCITY_MAX_PER_COMPANY=6`, `HITECHCITY_MAX_COMPANIES=60`, `HITECHCITY_MAX_EXT_WALLS=3`, `HITECHCITY_MAX_EXT_ATTEMPTS=12`, `HITECHCITY_CAREERS_KEYWORD_SEARCHES=4`, `ATS_CAPTCHA_POLL_SEC=0.4`, `ATS_OWNER_FOCUS_EVERY_SEC=2`.
4. LinkedIn: company-targeted **job** searches via `/jobs/search/?f_C=<companyId>&keywords=…&location=Hyderabad, Telangana, India&geoId=105556991&distance=25` (never company `/jobs/` alone — those pages lack clickable cards; never search campus strings like "Knowledge City" / "Raheja"). Keywords every run (EM-first, not architect-only): Engineering Manager, Technical Lead, Staff/Principal/Lead Software Engineer, Software Development Manager, Solution/Technical Architect, Principal .NET, Azure/.NET.
5. Easy Apply AND company-website / ATS redirects — both required paths
6. After a successful apply, try referral: message the job poster (poster-specific Message) OR send a short LinkedIn connection note to a Hyd engineer/recruiter/EM at that company asking for a referral / 15–20 min screen
7. For each company (across parallel tabs): open official careers URLs from companies.json **rewritten every run** to (a) multi-role keywords EM/Tech Lead/Staff/Principal/SDM/Architect/.NET and (b) **Hyderabad ALWAYS** — invent/overwrite `location` / `loc` / `loc_query` / `city` / `locationsearch` / `lc` / `searchLocation` on every portal URL, then pin the on-page Location UI to Hyderabad after navigation. If a portal has no Hyd option (e.g. Intel Workday today), skip non-Hyd roles — never open Haifa/Bangalore/US. Find Hyd/India qualifying roles, COMPLETE Greenhouse / Lever / Workday / SmartRecruiters / SuccessFactors / company ATS when guest/logged apply is possible. iCIMS: fill Email + I accept + Next in nested `in_iframe=1` before captcha wait. Skip only clear non-Hyd / SSO-only hosts — never abandon a matching Hyd form mid-apply without `ASK_OWNER` wait.
8. Boards: each portal gets its own preflight + CDP launch + allowlist; keep per-board caps modest (defaults ~6–12). **Cutshort/Indeed are login-probed first** (`chrome_session.js check`) — skip immediately on `*_login_required` so the phase is not burned. Other board login walls → log blocked, continue.
9. External ATS: hard walls (captcha/login) use per-company wall caps (`HITECHCITY_MAX_EXT_WALLS=3` default). Soft incompletes do not burn matching inventory. Headed runs use longer ATS time caps + `ASK_OWNER` form wait (`ATS_CAPTCHA_WAIT_SEC`).
9b. Cap stuck captcha waits with owner poll 0.4s — **every daily run** keeps the captcha/ASK_OWNER tab focused (`owner_focus` / CDP `bringToFront`, re-activated every `ATS_OWNER_FOCUS_EVERY_SEC=2`) until you solve it; resume immediately after. Do **not** require a paid captcha-solver key. Optional `CAPSOLVER_API_KEY` only if the owner already set it.
10. Skip already Applied; expand inventory to 14-day window when thin
11. Discovery default: full campus catalog + web directory scrape every run; LinkedIn *company-name* slug search is **off by default** (`HITECHCITY_DISCOVERY_LINKEDIN=0`). Set `=1` only when refreshing slugs. Set `HITECHCITY_DISCOVERY_WEB=0` only to skip live REIT/Cityinfo fetches.
## Skip rules (TITLE-FIRST — do not over-filter)
Skip ONLY when the TITLE (or clear mandatory JD language) is wrong:
- Wrong-stack TITLE: Salesforce, ServiceNow, SAP/D365-primary, Guidewire, PEGA, Coupa, Revit/BArch, Hubspot, M365-only, GIS/Esri-primary, QA/SDET/Quality Engineering, BPO, pure AI/data title without .NET on the title
- Wrong-city TITLE/location pills: non-Hyd and not Remote/WFH
- Junior / intern / fresher titles
- JD says Java/Python/Node/Salesforce is **mandatory/required/only** (not a casual mention)
- Listed max CTC clearly under **35 LPA** (35–55 bands are OK — always state 60 expected)
- Company clearly outside the campus tenant list

DO NOT skip because the JD casually mentions Salesforce, SAP, Java, Data Engineer, or other stacks as adjacent teams/tools when the role itself is .NET / architect / lead / EM. Title wins over incidental JD text.

## Form mechanics
- Careers phase: **~10 companies in parallel tabs** (default). Within each worker tab, finish one form before opening the next job on that tab; close messaging overlays before Next/Submit. LinkedIn Easy Apply remains one job at a time on its tab.
- India (+91), CTC 52L current / 60L expected, notice 0
- Confirm Application submitted or ATS confirmation before counting success
- If LinkedIn login missing, stop and report LinkedIn login required (career-portal-only partial run is OK if some applies already landed)

## Report
Write `/opt/cursor/artifacts/hitechcity-daily.json` (+ discovery/careers/linkedin/boards sub-reports). Include submitted (company, role, job id/URL, location, Easy Apply vs career ATS vs board), referrals sent, skipped, blocked, discovery added. Totals. Call out campus names when known.

## Auto-fix & push (MANDATORY)
If you hit a code-fixable blocker (company list drift, career scraper, LinkedIn company filter, ATS filler, CDP/preflight), fix under tools/hitechcity or scripts/, append via `bash scripts/append-issue-fix.sh <portal> "issue" "fix"` (writes `automation-prompts/issues/<portal>.md` only — never the shared ISSUES file), commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. That merge helper then same-day re-runs this Hitech City job with the fix (`scripts/rerun-daily-after-fix.sh`) — do not wait for tomorrow's cron. Follow automation-prompts/AUTO_FIX.md. Do not invent applies. Owner-only: login walls, CAPTCHA/OTP, Automations UI paste for ONE_TIME_LOADERS.
```
