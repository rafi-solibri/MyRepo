# Issues from last cron + fixes

## Policy: auto-fix & push every daily run

See [AUTO_FIX.md](AUTO_FIX.md). Code-fixable blockers discovered during any daily
automation must be patched in durable helpers, pushed on a feature branch, and
opened as a draft PR — not left as report-only notes.

## Fixed for 2026-08-11 Foundit daily apply

| Issue | Fix |
| --- | --- |
| `tools/foundit/daily_apply.js` was login-only scaffold (0 Raven/Falcon applies) | Full runner: Raven public search → `classifyJob` → `userJobInfo`/`applicationStatus` eligibility → Falcon ****** → LinkedIn/ATS handoff; writes `/opt/cursor/artifacts/foundit-apply-report.json` |
| JD marketing "remote-first" overrode explicit Noida/Bangalore cities | `locationsFrom` only reads Hyd/remote from description when card locations are empty or country-only; test covers Noida false-pass |
| Runner hung on CDP after scaffold | Playwright `browser.close()` after connectOverCDP (disconnects without killing Chrome) |

## 2026-08-11 Hitech City / Knowledge City Daily

| Issue | Fix |
| --- | --- |
| No campus-focused daily (Knowledge City / Knowledge Park / Mindspace Madhapur) | Added `tools/hitechcity/` + `automation-prompts/08-hitech-city.md` for automation `b65968f7-953d-11f1-ba66-0e7d0216e441` |
| Career portals ignored vs job boards | `daily_apply.py` runs LinkedIn company-targeted applies + referrals, then company careers ATS |
| Untitled automation / missing loader | Documented rename + ONE_TIME_LOADERS paste (owner must paste — API read-only) |
| False `linkedin_login_required` from footer “Sign in” text | Login check uses nav/me photo + URL walls (`/login`, authwall), not body substring |
| Career scraper opened US roles / Amazon passport walls | Bad-city link filter + `passport.amazon.jobs` auth-host detection; skip non-Hyd before ATS burn |
| LinkedIn AI job search removed classic `job-card-container` list | `linkedin_target_apply.py` uses `/company/{slug}/jobs/` HTML job IDs → `/jobs/view/{id}` apply path |
| `card_meta` JS shadowed `location` / empty role on new job view | Renamed to `locText`; parse `document.title` + content lines under nav chrome |
| Location false-skip: bare `hitec` matched inside “Architect” | Word-boundary / `hitec city` tokens only; prefer explicit city lines |
| External Apply missed on new job view | Match `<a aria-label="Apply on company website">` + exact Apply link/button |

## Fixed for 2026-08-10 Indeed SmartApply (post-Cloudflare)

| Issue | Fix |
| --- | --- |
| Easy Apply stuck on `questions-module` (Continue never clicked) | Hardened `fill_common_questions` in `uc_daily_apply.py`: React InputEvents, radio-group defaults, required text/select fill, iframe awareness |
| Review step clicked **Preview what the employer sees** and trapped in `about:srcdoc` | CTA scorer excludes Preview/Edit/Download; skip `about:` frames; dedicated `submit_review_application()` |
| `daily_apply.js` timed out / failed to parse UC stdout logs | Parse JSON tail; read `indeed-daily-run.json` artifact; raise UC timeout default to 30m |
| Remaining: Google **reCAPTCHA** (“I'm not a robot”) on Review → Submit | Attempt `uc_gui_click_rc` / frame-targeted GUI click; if unsolved mark `easy_apply_recaptcha` and continue (CAPTCHA wall — not invent applies) |

## Fixed in this repo

| Issue | Fix |
| --- | --- |
| Cloud Indeed Cloudflare **Request Blocked** / Turnstile on datacenter IPs | **WARP SOCKS `127.0.0.1:40000` + SeleniumBase UC + `uc_gui_click_captcha()`**. Scripts: `scripts/start-warp-proxy.sh`, `tools/indeed/cf_bypass_uc.py`, hybrid profile prep (`prepare_uc_profile.py` strips burned `cf_*` cookies). Preflight auto-starts WARP+UC. Plain Chrome CDP through WARP still hard-blocks — use UC path (`uc_daily_apply.py`). |
| `Rafi_Resume_Architect.docx` missing → agents invented stubs or used portal-only resume | Canonical **`resumes/Rafi_Resume.docx`** (your upload) + `scripts/bootstrap-job-assets.sh` copies to Documents/resumes/Downloads; legacy Architect filename is a same-file alias |
| LinkedIn Easy Apply looked for Architect label | Scripts use label **Rafi_Resume**; external ATS uploads canonical docx |
| Cutshort questionnaires locked empty (9/11) | Documented correct API payload in `tools/cutshort/questionnaire.js` — never `screeningSubmitted` before verified answers |
| Naukri Coupa/Pega / Intern≈Internet false applies | Filters in `tools/naukri/resume_and_filters.js` |
| Foundit `canJobApply` accidental submit | Explicit forbid in `tools/foundit/resume.js` + prompts |
| LinkedIn Bengaluru false-allow via page body "Hyderabad" | Prompts: location from top card / workplace pills only |
| Agents rediscovering tools each run | Durable helpers under `tools/linkedin`, `tools/cutshort`, `tools/naukri`, etc. |
| Naukri profile resume not refreshed daily | `tools/naukri/update_profile_resume.js` + STEP 0 in Naukri prompt re-uploads `Rafi_Resume.docx` every run for recruiter freshness |

## Fixed for 2026-08-06 “automations did not run”

| Issue | Fix |
| --- | --- |
| Cron fired but 0 applies (login walls) | Agents used empty CDP profiles while you logged into Default Chrome |
| Session mismatch | `scripts/sync-chrome-sessions.sh` + `tools/chrome_session.js` copy Default → all portal CDP profiles |
| Naukri false-skips on SA roles | Title skip no longer matches bare `QA`; detail scans must not use full `document.body` |
| General Daily noise | Documented: **disable** General Daily (research-only, 0 applies) |

## Fixed for 2026-08-06 reliability pass

| Issue | Fix |
| --- | --- |
| Session sync could wipe a previously authenticated CDP profile when Desktop Default lacked that portal cookie | `scripts/sync-chrome-sessions.sh` is now non-destructive and preserves authenticated destinations |
| Portal jobs started without a consistent resume/session check | `scripts/preflight-portal-run.sh <portal>` bootstraps assets, syncs safely, verifies resume, and exits clearly on login-required |
| Ad-hoc Chrome CDP launch caused `ECONNREFUSED` / wrong profile risks | `scripts/launch-chrome-cdp.sh <portal>` starts port 9222 with the correct synced profile |
| Notification fallback script referenced by prompts was missing from main | Added `scripts/send-job-status-email.mjs` with `RESEND_FROM_EMAIL` or documented onboarding fallback |
| Indeed failures wasted apply time behind Cloudflare | `tools/indeed/preflight.js` detects public-cloud Cloudflare blocks and reports private worker required |
| Indeed/Instahyre resume verifier commands were silent | `node tools/indeed/resume.js` and `node tools/instahyre/resume.js` now print JSON |

## Fixed for 2026-08-06 login diagnosis (this PR)

| Issue | Fix |
| --- | --- |
| Saved snapshot only had Cutshort auth; LinkedIn/Naukri/Foundit/Instahyre/Indeed missing | Documented live cookie audit in `ENV_READINESS.md`; added `scripts/verify-portal-logins.sh` |
| Hard to complete Desktop logins correctly | `scripts/open-portal-login-tabs.sh` + `scripts/portal-login-checklist.html` open Default Chrome with all 6 portals |
| “Saved environment” confused with “sessions captured” | Checklist / verify script require auth cookies before declaring ready |

## Fixed for 2026-08-10 blocker pass

| Issue | Fix |
| --- | --- |
| Naukri resume re-upload did not confirm “Updated today” (`todayHit: false`, empty `updateOn`) | Hardened `tools/naukri/update_profile_resume.js`: resume-only file inputs, Update-resume click + filechooser, headline soft-touch with `RESUME_HEADLINE`, retries, stricter verify; exit 5 if unconfirmed |
| Agents sometimes skipped STEP 0 or only uploaded once | `tools/naukri/daily_apply.js` now **always runs** profile resume refresh before applies (`profileUpdated` in counts) |
| Capgemini-style Foundit false apply (title “6-9 Yrs” vs Raven 0-0) | Added `tools/foundit/filters.js` (+ tests) with title experience-band parsing |
| LinkedIn weak/wrong-domain Easy Applies (Revit / Hubspot / M365 / AI Architect) | Expanded `BLACKLIST` / `TITLE_OK` in `tools/linkedin/linkedin_easy_apply.py` |
| Instahyre “Quality Engineering Lead” filter slip | Added `tools/instahyre/filters.js` + prompt HARD skip |
| Hirist login counted as hard blocked | Naukri external path skips Hirist login walls (`hirist_login_required_skip`) |
| Indeed Cloudflare only vaguely documented | Added `INDEED_CLOUDFLARE.md` / home-cron helpers; `launch-chrome-cdp.sh` honors `INDEED_HTTP_PROXY` |
| Daily mail ignored home Indeed applies (only showed cloud Cloudflare 0) | Home cron writes/publishes `indeed-daily-run.json` to `automation-results`; Notification prompt fetches via `scripts/fetch-indeed-home-result.sh` and includes applied/rejected/blocked/skipped |

## Fixed for 2026-08-10 volume / false-skip pass

| Issue | Fix |
| --- | --- |
| LinkedIn JD blacklist false-skip (S&P Global .NET Director → `Data Engineer`) | `tools/linkedin/filters.py`: title-first blacklist; JD only for mandatory/required stacks |
| LinkedIn TITLE_OK too narrow + MAX_APPLY=30 | Broader titles (Software/Cloud/Azure Architect, Lead SWE, Director); MAX_APPLY=50, MAX_EXTERNAL=25, 14-day TPR |
| LinkedIn PRIORITY_IDS skipped when missing from Easy Apply scan | Always queue `PRIORITY_IDS` in `linkedin_external_apply.py` |
| LinkedIn Greenhouse Easy Apply stuck (education/LinkedIn URL/checkboxes/no time-cap) | Greenhouse filler + 3-min time-cap in `linkedin_easy_apply.py` |
| Naukri 0 applies: CTC floor 50 skipped 30–40 LPA .NET Architect/Lead | Floor lowered to **35 LPA**; forms still state 65 expected |
| Naukri `skip_no_dotnet` on Architect/Lead cards without .NET snippet | Architect/Lead/EM/Principal/Staff allowed without card .NET proof |
| Naukri would false-allow pure AI Architect after archLead waiver | `shouldSkipTitle` skips AI/data titles without .NET on title |
| Foundit over-skip on seniority / CTC&lt;50 / maxExp | Senior .NET seniority; CTC floor 35; keep Capgemini 6-9 reject |
| Cutshort free-text questionnaires locked empty | `questionnaire.js` free-text via `responseStringArray` + empty `responseNumberArray` |
| Cutshort / Foundit / Instahyre / Indeed reinvent flows each run | Durable `daily_apply.js` runners (+ filters) under each portal |
| Indeed preflight HTTP-only (proxy ignored in Chrome) | `chrome_probe.js` + proxy-aware `preflight.js`; Windows home task installer |
| Agent prompts over-filtering (“listed max ~15–50”, soft stop ~20) | Apply-bias + title-first + aim 40–50+ across `automation-prompts/0*.md` |
| Stale ENV_READINESS “5/6 missing logins” | Updated for session-seed reality |

## Fixed for 2026-08-10 Indeed Easy Apply 0-submit

| Issue | Fix |
| --- | --- |
| Cloud runs reached review but 0 applied (`easy_apply_recaptcha` / `easy_apply_incomplete`) | Ported audio reCAPTCHA solver + direct checkbox click from `cursor/indeed-daily-apply-job-e0ec`; recognize `/post-apply`; scroll-to-Submit; treat checkbox-checked as cleared; longer job timeout; install `SpeechRecognition`/`pydub` in `cloud-agent-install.sh` |
| SmartApply reCAPTCHA clicked footer badge / FileLock deadlock / audio rate-limit → 0 submits | Prefer SmartApply sitekey `6Ldn8Qwp` (skip footer `6Lcr30sp`); `post-apply` confirmation; submit-only CTA; filelock singleton + avoid nested `uc_gui_*`; audio rate-limit cool-down/dismiss; `SpeechRecognition` in install |

## Fixed for 2026-08-10 Indeed preflight false exit 5

| Issue | Fix |
| --- | --- |
| Cloud cron stopped with Cloudflare exit 5 even though WARP+UC had already cleared (`Welcome, MOHAMMED`) | SeleniumBase printed `uc_driver` download noise on **stdout** before JSON; `preflight.js` `JSON.parse` failed → false `ucBypass.ok=false`. Now: lenient JSON extract + read `indeed-cf-bypass.json`; `cf_bypass_uc.py` / `uc_daily_apply.py` redirect SB chatter to stderr and emit JSON on `sys.__stdout__` |

## Fixed for 2026-08-11 Indeed Turnstile flaky exit 5

| Issue | Fix |
| --- | --- |
| Cloud cron exit 5 after yesterday’s green run: Turnstile widget visible (`Verify you are human`) but clicks did not clear → hard stop | Root cause: **filelock 3.32** deadlocks nested SeleniumBase `uc_gui_*` locks — old patch set `is_singleton` in `__init__` too late (metaclass decides earlier). New `tools/indeed/filelock_patch.py` wraps `FileLockMeta.__call__`. Also: wait for Turnstile, multi-strategy CF clicks + manual XY fallback, window focus, WARP IP **rotate** between rounds, `preflight.js` UC retries. |

## Fixed for 2026-08-10 Hotel Price Tracker

| Issue | Fix |
| --- | --- |
| Google Hotels inventory returned 0 offers from cloud (pages show `$` not `₹`) | `providers/google_hotels.py` parses USD and converts via `DEFAULT_USD_INR` (~87); skips UI chips |
| Calendars were Kayak-only (missed lower Google ladder rates) | New `calendar_google.py` enriches Qualia/Oak nights; `AUTOMATION_PROVIDERS=("kayak","google")` |
| Google `$7` UI crumbs became fake ₹609 calendar mins | Reject USD &lt; `$12` / INR &lt; ₹1000 in Google parsers |
| Same-day Resend idempotency key collision on cron re-run | Idempotency key now includes `HHMMSS` stamp in `automation.py` |

## Fixed for 2026-08-11 Windows private worker crash

| Issue | Fix |
| --- | --- |
| `agent worker start` on Windows dies: `better-sqlite3` NODE_MODULE_VERSION **127 vs 137** / `Error starting exec-daemon` | **Not fixable by reinstall** — Cursor Windows worker package bug ([forum](https://forum.cursor.com/t/windows-remote-control-worker-crashes-better-sqlite3-node-module-version-127-vs-137-cursor-3-15-6/167841)). Workaround: run Linux worker under **WSL**. Scripts: `scripts/fix-windows-agent-worker.ps1` (−LaunchWsl) + `scripts/setup-wsl-agent-worker.sh --name job-apply-laptop`. Do not pipe the Linux `curl \| bash` installer in PowerShell ISE. |
| Wrong installer in PowerShell ISE (`curl … \| bash`) | Docs + repair script point to WSL bash or `irm 'https://cursor.com/install?win32=true' \| iex` |

## Still requires your action (cannot fix from code alone)

| Blocker | Who | What to do |
| --- | --- | --- |
| Windows `agent worker start` ABI crash (127/137) | You | Until Cursor ships a fixed Win package: `wsl --install -d Ubuntu` → `powershell -ExecutionPolicy Bypass -File scripts\fix-windows-agent-worker.ps1 -LaunchWsl` (or `bash scripts/setup-wsl-agent-worker.sh --name job-apply-laptop` inside WSL). Leave WSL terminal open; pick that machine in Agents. |
| Snapshot missing portal logins | You | `bash scripts/open-portal-login-tabs.sh` → sign in on Desktop → quit Chrome → `bash scripts/verify-portal-logins.sh --strict` → **Save/Update snapshot** |
| Indeed Cloudflare 403 if WARP+UC fails | You | Prefer cloud path: WARP SOCKS + `cf_bypass_uc.py` (auto in `preflight.js`). Fallback: `scripts/indeed-home-daily.sh` / residential `INDEED_HTTP_PROXY` |
| Hirist secondary board login | Optional | Log into Hirist in Desktop Chrome and re-seed sessions if you want Hirist applies |
| Workday / Greenhouse OTP ATS walls | Optional | Keep Gmail logged in same Chrome profile; complete OTP once per ATS |
| Verified notification sender missing | You | Set secret `RESEND_FROM_EMAIL` to a verified sender; fallback uses `Job Status <onboarding@resend.dev>` |
| General Daily duplicate | You | Keep disabled: https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441 |
| Indeed home results → daily mail | You | Keep home cron on; ensure home PC can `git push origin automation-results`; re-paste Notification loader from `ONE_TIME_LOADERS.md` once |
| Re-paste Agent instructions | You | Automations API is read-only. For Indeed, paste the short loader from `ONE_TIME_LOADERS.md` (or the full `06-indeed.md` fence) into https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441 and Save. Morning 2026-08-11 cron still used an older short prompt. |

## After merging this PR

1. Re-paste updated prompts from `automation-prompts/0*.md` into each automation (resume section changed).
2. Merge to `main` (or point automations at this branch) so cron checkouts include `resumes/Rafi_Resume.docx`.
3. Complete portal logins + snapshot once.
4. For Indeed: enable private worker.
5. For Notification: connect Resend MCP + `RESEND_FROM_EMAIL`.
