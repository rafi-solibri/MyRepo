# Issues from last cron + fixes

## Fixed for 2026-08-13 LinkedIn cloud cron

| Issue | Fix |
| --- | --- |
| SQLite/`verify-portal-logins` reported OK while live CDP hit `/login` then `/checkpoint` (stale `.portal-sessions` `li_at` from 2026-08-06); Easy Apply stopped correctly but external burned 25 PRIORITY_IDS as false `no external Apply button` | `launch-chrome-cdp.sh` hard-fails LinkedIn live probe when `CDP_REQUIRE_LIVE_LOGIN=1` (default); headed-login scripts set `=0`; external helper auth-gates before PRIORITY_IDS; Easy Apply exits 5 on CDP/login wall; verify script notes SQLite≠live. Owner: headed login + refresh `.portal-sessions` + Save snapshot |

## Fixed for 2026-08-13 Foundit daily (cloud)

| Issue | Fix |
| --- | --- |
| Raven `minimumExperience/maximumExperience` `0-0` (undisclosed) with no title band was kept as `max=0` → false skip `maxExp 0<10` (e.g. Senior Software Architect - .NET) | `experienceBounds` returns NaN/NaN + `undisclosed:true` when Raven is 0-0 and title has no band; still overlays title bands like 6-9 / 8-12 |
| Country-only `locations: India` failed as `location not Hyd/remote: India` without JD enrich → missed Remote/Hyd in description | `classifyJob` sets `needsEnrich` for empty/country-only India when description missing |

## Fixed for 2026-08-12 Notification home (Windows residential)

| Issue | Fix |
| --- | --- |
| `send-job-status-email.mjs` failed with `UNABLE_TO_GET_ISSUER_CERT_LOCALLY` under corp SSL inspection | Auto-retry once with `NODE_TLS_REJECT_UNAUTHORIZED=0`; optional `RESEND_INSECURE_TLS=1` |

## Fixed for 2026-08-12 Hitech City home (Windows residential)

| Issue | Fix |
| --- | --- |
| Preflight `liveHint` / docs said `home-headed-login.sh hitechcity` but the script rejected that portal (usage exit 2) | Accept `hitechcity` as LinkedIn alias (same CDP session + `wait_for_cdp_login.js`); hint also points at `linkedin` |
| Careers mid-run crash on Windows cp1252 console: `UnicodeEncodeError` printing role with `ā` (Qualcomm) aborted whole careers phase | `configure_windows_stdio` in `daily_apply.py` + `_safe_print` in `careers_apply.py` |

## Fixed for 2026-08-12 Naukri home (Windows residential)

| Issue | Fix |
| --- | --- |
| Preflight exit 3 (`chrome_cookies_locked` / no SQLite `nauk_rt`) while live Naukri homepage was already logged in | Added `tools/naukri/wait_for_cdp_login.js`; wired into `chrome_session` LIVE_CDP_WAITERS + `home-headed-login.sh naukri` |
| Hirist CTAs stuck as `external_link_not_opened` (“Apply on hirist.com Apply attempted”) | Soft-skip `hirist_login_required_skip` when CTA mentions hirist before hard-block |
| SRE/DevOps-primary titles burned ATS time (Apple SRE EM, Arcesium Principal SRE) | `shouldSkipTitle` skips `\bsre\b` / site reliability / devops engineer|lead |
| Workday Autofill chooser + cookie banner timed out; branded hosts (`jobs.rsmus.com`) missed Workday helper | Stronger cookie dismiss, Autofill→Manual fallback, detect Workday UI via `data-automation-id` / chooser text |
| Home resume path preferred `/workspace/...` stub | `findResume` prefers repo `resumes/Rafi_Resume.docx` |

## Fixed for 2026-08-12 Cutshort home (Windows residential)

| Issue | Fix |
| --- | --- |
| Preflight `chrome_session check cutshort` exit 3 (`chrome_cookies_locked` / no SQLite `cutshort_authentication`) while live CDP dashboard was already logged in | `checkPortal` live-CDP fallback now covers cutshort/foundit/instahyre (same pattern as LinkedIn) via each portal’s `wait_for_cdp_login.js` |

## Fixed for 2026-08-12 LinkedIn home (Windows residential)

| Issue | Fix |
| --- | --- |
| Home LinkedIn blocked on Security Verification; `--open-login` navigated away from checkpoint CAPTCHA tabs onto `/login` | `wait_for_cdp_login.js` prefers existing LinkedIn challenge tabs and never leaves checkpoint/challenge; system-mode hint |

## Fixed for 2026-08-12 Foundit home (Windows residential)

| Issue | Fix |
| --- | --- |
| Home Foundit daily stopped: live CDP had no `MSSOAT`; unauthenticated UI kept landing on `/rio/sign-out` (“Logged out Successfully”) after ~4 min poll | Added `tools/foundit/wait_for_cdp_login.js` + wired `home-headed-login.sh foundit`; owner must sign in once in headed system Chrome |

## Fixed for 2026-08-12 Naukri daily (cloud) — company-site CTA

| Issue | Fix |
| --- | --- |
| Company-ATS jobs blocked as `external_link_not_opened` because TopTier uses **Go to company site** (window.open) while **Apply on company site** is often disabled (“Apply attempted”) | `daily_apply.js` `handleExternal`: prefer Go-to CTA, skip disabled Apply, hook `window.open`, treat new non-Naukri pages as ATS; card/detail collectors match Go/Apply-on company site |

## Fixed for 2026-08-12 Naukri daily (cloud)

| Issue | Fix |
| --- | --- |
| Workday Candidate Home SSO chooser hid email/password → helper skipped auth and timed out on Next | `workday_apply.js`: click **Sign in with email**, prefer **Create Account**, use `signInSubmitButton` / create submit |
| `NAUKRI_WORKDAY_PASSWORD` (9 chars) fails Synchrony/etc Create Account (min 12 + complexity) | Detect `ats_password_policy`; owner must set a 12+ char Workday password in secrets |
| Workday host match missed `*.myworkdaysite.com` | `daily_apply.js` includes `myworkdaysite.com` in Workday ATS path |
| Post-create `/login` bounce re-clicked Create Account; `keyboard.type` mangled `%` in passwords | Prefer **Sign In** after create; `typeInto` uses `pressSequentially` / fill |
| Dashboard secrets not hot-reloaded into already-running agent VMs | Documented: new secret needs **new Cloud Agent / next cron** boot |

## Fixed for 2026-08-12 Hitech City cloud cron

| Issue | Fix |
| --- | --- |
| LinkedIn external ATS hung on Phenom reCAPTCHA iframes (body text missed “captcha”) → Blackbaud grind burned the run | `ats_fill.blocked_wall` detects reCAPTCHA/hCAPTCHA frames first; `attempt_ats_apply` bails before fill; EXT time cap 90s |
| After 2 CAPTCHA/login walls still opened every company-website apply for same tenant | Cap EXT walls per company (`HITECHCITY_MAX_EXT_WALLS`, default 2) and skip remaining EXT |
| Product Manager / Network Architect / GPU-kernel titles matched `TITLE_OK` via principal/architect | `LI_TITLE_SKIP` + careers skip for those stacks |
| Location check used `bodyHead` (sidebar/footer) contrary to top-card HARD rule; empty loc over-skipped | Top-card-only location; empty loc → apply bias |
| Bare `[data-sitekey]` false-positive CAPTCHA blocked Qualcomm Hyd careers; MSFT UK Reading card slipped | Visible reCAPTCHA iframe only; `BAD_LOC_HINT` adds United Kingdom/Berkshire/Reading |
| LinkedIn `ERR_HTTP_RESPONSE_CODE_FAILURE` wiped company searches + referrals; Easy Apply hung | `goto_retry` backoff; Easy Apply 120s time cap + recaptcha detect |
| Blackbaud Phenom `ats_incomplete_or_stuck` loop burned the run (wall cap ignored incompletes) | Count incomplete/time_cap toward walls; hard `MAX_EXT_ATTEMPTS` per company (default 3) |
| Microsoft careers cards in Romania/Bucharest opened before skip | `BAD_LOC_HINT` adds Romania/Bucharest (+ peer EU cities) |
| `tools/chrome_session.js` `checkPortal` used Python `def` → `SyntaxError` broke `preflight-portal-run.sh hitechcity` | Restored JS `function checkPortal(portal)` |
| `scripts/resolve-python.sh` expanded bare `$LOCALAPPDATA` under `set -u` → preflight aborted on Linux after cookie sync | Guard with `${LOCALAPPDATA:-}` / skip empty Windows candidate paths |
| Careers scraper opened US cards (Meta Austin/Seattle, MSFT Redmond, ModMed Boca) because full-page body “India” bypassed location HARD filter | `card_location_ok` uses role + top-card only; expand `BAD_LOC_HINT`; drop body-India bypass; skip wrong titles (system test / project analyst / …) |
| ModMed Workday URL `/Boca-Raton-FL/` still opened when title omitted city; Amazon apply ended on passport as `ats_incomplete_or_stuck` | Decode URL path via `url_loc_hint` into location check; classify `passport.amazon.jobs` as login/account wall |

## Fixed for 2026-08-12 Indeed daily (cloud)

| Issue | Fix |
| --- | --- |
| SmartApply review hung 4+ min per job: `clear_recaptcha` slept through Google audio rate-limit (240s) inside `submit_review_application`, so inventory stalled on one `review-module` | Drop cooldown sleep; bail with `easy_apply_recaptcha` after 1–2 attempts; honor job deadline; try CapSolver/2Captcha only when keyed |
| Review screenshot showed green reCAPTCHA + Submit but still `easy_apply_incomplete` (JS/SB click no-op) | Add `_gui_click_submit` PyAutoGUI trusted click when captcha already cleared |
| Voluntary self-ID / long employer privacy walls (e.g. Mattel) stuck Continue | Prefer Decline/Prefer-not answers; scroll past legal wall before fill/Continue |
| Questions CTA **"Review your application"** never clicked; required privacy ack checkboxes left unchecked → `questions_stuck` at 90% | Add CTA label; tick confirm/agree/privacy checkboxes in `fill_common_questions`; loosen reject regex so `edit` does not match unrelated CTAs |
| Demographic module clicked **Review your application** 20+ times without navigation (validation wall) | Abort Easy Apply after 3 identical CTA/url streaks (`cta_stuck`) |
| `tools/chrome_session.js` used Python `def checkPortal` → SyntaxError; Indeed portal preflight + `daily_apply.js` could not load `resolvePython` | Restored valid JS `function checkPortal` (same as Foundit/Cutshort/Instahyre) |

## Fixed for 2026-08-12 Instahyre daily (cloud)

| Issue | Fix |
| --- | --- |
| `daily_apply.js` only used `job_search` and missed recommended Hyd roles on `/candidate/opportunities/` (e.g. Uber Senior Staff Engineer) | Sweep undecided `candidate_opportunity/?status=0` first via `normalizeOpportunity` + same `skipReason` / apply path |
| Preflight `node tools/chrome_session.js check instahyre` crashed: `SyntaxError: Unexpected identifier 'checkPortal'` (`def checkPortal`) | Restored JS `function checkPortal(portal)` in `tools/chrome_session.js` (same fix as Foundit/Cutshort) |
| Preflight aborted after sync: `scripts/resolve-python.sh: LOCALAPPDATA: unbound variable` (`set -u` on Linux) | Guard with `${LOCALAPPDATA:-}` / skip empty Windows candidate paths |
| Search-apply slipped AWS Administrator / Azure Virtualisation / Data Specialist (cloud keyword bypassed generic IC skip) | `filters.js`: hard-skip `ops_admin_title` + `data specialist` in pure AI/data gate |

## Fixed for 2026-08-12 Cutshort daily (cloud)

| Issue | Fix |
| --- | --- |
| Preflight `chrome_session check cutshort` crashed: `SyntaxError: Unexpected identifier 'checkPortal'` at `tools/chrome_session.js:227` (`def checkPortal`) | Restored valid JS `function checkPortal(portal)` so portal auth checks and Cutshort preflight can run |
| `classify` used `\bc#\b` / `\b\.net\b` → never matched skills/titles like `C#` / `Senior .NET` → 0 qualifying after 1958 scan | `NET_STACK_RE` / `STACK_SIGNAL_RE` without broken `#` word-boundaries; expand tier1 for `Engineering Leader` / `Head of Engineering`; `\bsap\b` hard-skip; `tools/cutshort/test_filters.js` |

## Fixed for 2026-08-12 Foundit daily (cloud)

| Issue | Fix |
| --- | --- |
| `hasSeniority` required `Senior` before software/.NET/engineer only → false skips for `.Net Senior Developer`, `Senior Backend Developer (.NET)` | Broaden to `\bsenior\b` / `\bsr\.?\b` (still gated by .NET + Hyd/remote + exp) in `tools/foundit/filters.js` + tests |
| Workday redirect (`APPLY_REDIRECT_STAGE_ONE`) stalled on job page → `ats_incomplete_or_cap` without Apply/Apply Manually | `daily_apply.js` ATS handoff: click Workday Apply → Apply Manually, Autofill/Select Files, Next/Submit automation-ids; Create Account/Sign In step → `ats_login_wall` (owner) |
| `tools/chrome_session.js` used Python `def checkPortal` → SyntaxError; every portal preflight failed | Restored valid JS `function checkPortal` so `preflight-portal-run.sh` / `chrome_session.js check` load again |
| `confirmLogin` on `/seeker/dashboard` false-failed (`Hi, Seeker` before header personalizes) despite live MSSOAT + `/home/user` Hi Rafi | Poll dashboard then fall back to `/home/user`; ignore transient Seeker greeting |

## Fixed for 2026-08-12 Naukri daily (cloud)

| Issue | Fix |
| --- | --- |
| Same `LOCALAPPDATA` unbound abort hit Naukri preflight before STEP 0 | Confirmed Instahyre/main guard (`${LOCALAPPDATA:-}` / skip empty Windows paths); Naukri cron continued after merge |

## Fixed for 2026-08-12 LinkedIn cloud cron

| Issue | Fix |
| --- | --- |
| Preflight crashed: `tools/chrome_session.js` had Python `def checkPortal` inside Node → SyntaxError before cookie check | Restored `function checkPortal(portal)` (also fixed via Foundit PR #79) |
| Preflight crashed: `scripts/resolve-python.sh` expanded unset `LOCALAPPDATA` under `set -u` on Linux | Guard with `${LOCALAPPDATA:-}` / skip empty Windows candidates (also on main via Instahyre #82) |
| `pkill -f chrome` / `pkill -f remote-debugging-port=9222` matched the agent bash cmdline and aborted CDP launch/sync mid-run | Added `scripts/kill-chrome-cdp.sh` (exe+/proc filter); launch + sync use it; reuse CDP only when user-data-dir matches |
| Easy Apply hung after first `/jobs/view/{id}` navigation: search-card locators went stale and next-card loop sat in `ep_poll` | `process_search` restores the search URL + rebinds card locators after each apply/block |
| Mid-batch crash on `Page.goto` `net::ERR_HTTP_RESPONSE_CODE_FAILURE` (LinkedIn 429/999) left no `apply-report.json` | Retry search navigation 3× with feed cool-down; always write report in `finally` |
| External helper blocked many priority IDs on same LinkedIn HTTP failures (single retry only) | `linkedin_external_apply.py` retries job-view goto 3× with feed cool-down |


## Fixed for 2026-08-11 Windows owner-action blockers

| Issue | Fix |
| --- | --- |
| Windows Chrome ABE blocked Default→CDP cookie copy → every portal needed headed re-login | Home Windows defaults `CHROME_CDP_MODE=system` — launch CDP against real `Chrome\\User Data` + `Default` (PowerShell Start-Process); reuse one Chrome for all portals |
| Leftover empty CDP on :9222 reused by mistake | `launch-chrome-cdp.sh` verifies system user-data-dir before reuse |
| Hitech City missing from home schedule / Windows report path | `hitechcity` in portal-home-daily + Task Scheduler; `daily_apply.py` writes `artifacts/hitechcity-daily.json` when `/opt/cursor` absent |
| Resend email not sent (MCP unauth + no API key) | Authenticate Resend MCP; create sending key; set user env `RESEND_API_KEY` + `RESEND_FROM_EMAIL` |
| Multi-portal login UX | `scripts/home-headed-login-all.sh` opens all login tabs on system Chrome CDP |

## Policy: auto-fix, push, and merge every daily run

See [AUTO_FIX.md](AUTO_FIX.md). Code-fixable blockers discovered during any daily
automation must be patched in durable helpers, pushed on a feature branch, opened
as a **ready** PR (not draft), and merged with `bash scripts/auto-merge-fix-pr.sh`
— not left as report-only notes.

## Fixed for 2026-08-11 Cutshort home (Windows residential)

| Issue | Fix |
| --- | --- |
| Home Cutshort blocked: SQLite `destHasAuth: true` for `cutshort_authentication` but live CDP redirected to `/?redirect_url=…` (stale session) | `tools/cutshort/wait_for_cdp_login.js` live dashboard probe; `home-headed-login.sh cutshort` uses it; owner: sign in on headed CDP profile |
| Waiter false-green: brief `/profile/candidate-dashboard` URL before redirect + sparse "Find jobs" text | Waiter settles URL ~6s and requires dashboard body signals (Matches/Applications/Edit profile), not marketing chrome |

## Fixed for 2026-08-11 LinkedIn home (Windows residential)

| Issue | Fix |
| --- | --- |
| Home LinkedIn blocked: Windows ABE cannot sync Desktop `li_at`; SQLite “preserved” `linkedin-alt` auth was stale and Chrome dropped it on load | `tools/linkedin/wait_for_cdp_login.js` live CDP probe; `launch-chrome-cdp.sh` opens login + warns; `chrome_session.js` prefers alt only when primary lacks `li_at` name and clarifies ABE headed-login reason; owner: `bash scripts/home-headed-login.sh linkedin` |
| Preflight `chrome_session check linkedin` exit 3 while live CDP has `li_at` (Cookies DB locked / ABE) | `checkPortal` falls back to `wait_for_cdp_login.js` live probe on Windows / locked SQLite |
| Easy Apply CTA is `<a aria-label="Easy Apply to this job">` (hashed classes); helper only matched `<button>` → false `no Easy Apply button` | `linkedin_easy_apply.py` matches anchor CTAs, opens `/jobs/view/{id}`, force/mouse click |
| Account toast “You reached today’s Easy Apply limit” looked like click no-op | Detect limit toast → `easy_apply_daily_limit` blocked + stop batch; dismiss Got it |
| External runner crashed when `apply-report.json` missing | `linkedin_external_apply.py` continues with `PRIORITY_IDS` only |
| Windows Python `/opt/cursor` is `C:\opt\…` while Git Bash uses `Programs\Git\opt\…` (split artifact trees) | LinkedIn helpers prefer repo `artifacts/` on Windows; goto retry + per-job catch |
| External Apply CTA also hashed `<a aria-label="Apply on company website">` | Expanded external button selectors |

## Fixed for 2026-08-11 Notification home fetch (Windows)

| Issue | Fix |
| --- | --- |
| `fetch-home-result.sh` wrote under Git `/opt/cursor/artifacts` then Node opened `C:\opt\...` (ENOENT) so Notification Job could not `cat` JSON | On MSYS/MinGW default cache to `$ROOT/artifacts`; pass `cygpath -m` paths into Node via `process.argv` |

## Fixed for 2026-08-11 Indeed Windows home runner

| Issue | Fix |
| --- | --- |
| Home Windows `chrome_probe.js` → `chrome_not_found` (linux-only `command -v`) | Resolve `chrome.exe` via `ProgramFiles` / `path.join`; Windows probe kill via PowerShell; use `resolvePython()` (not Store stub) |
| Indeed CDP handshake 403 without `--remote-allow-origins=*` | `launch-chrome-cdp.sh` + probe add `--remote-allow-origins=*` |
| Home Indeed hard-required WARP SOCKS (unavailable on Windows) → exit 2 / abort | `INDEED_SKIP_WARP=1` on Windows home (`portal-home-daily.sh`); preflight/UC/launch continue direct on residential IP; seed profile from `~/.cursor/chrome-cdp-profiles/indeed` |
| `daily_apply.js` / UC helpers called Store-stub `python3` | Prefer `C:\Python314\python.exe` / `resolvePython()` / `sys.executable` |
| Indeed `hasAuth` true on anonymous `CTK` alone → false ready | Require `__Secure-PassportAuthProxy-BearerToken` only |

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

## Fixed for 2026-08-11 Instahyre daily apply

| Issue | Fix |
| --- | --- |
| Instahyre broad skill waves applied to weak pure AI/frontend/full-stack roles without .NET/cloud proof | `tools/instahyre/filters.js` now hard-skips pure AI/data and frontend-only titles without .NET, and requires .NET/C# or senior cloud/platform evidence for generic engineer/developer titles |
| `daily_apply.js` only scaffolded login then hung on CDP | Full job_search + `skipReason` + apply API loop; incremental report; `process.exit` (no `browser.close`/`disconnect` hang) |
| Filter slips: Anaplan / Kinaxis / `Solution Architect - AI` / Data Analyst / Operations Manager | Tightened `tools/instahyre/filters.js` title-first skips |
| Spot-check treated Coupang Facebook/Instagram as external ATS | Ignore social hosts; require apply/ATS URL patterns |

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

## Fixed for 2026-08-11 Naukri home (Windows residential)

| Issue | Fix |
| --- | --- |
| Preflight looked for `/home/ubuntu/.config/google-chrome` + `Default/Cookies` | `tools/chrome_session.js` + `scripts/sync-chrome-sessions.sh` resolve Windows `User Data` and `Default/Network/Cookies`; home CDP defaults to `~/.cursor/chrome-cdp-profiles/<portal>` |
| `launch-chrome-cdp.sh` missing `chrome.exe` / Store-stub `python3` | Resolve Chrome under Program Files; headed by default on Windows; `py -3` / `Python314` fallbacks |
| Cookie-name `hasAuth` true but Naukri still on `nlogin` | Chrome **v20 App-Bound Encryption** — profile copy cannot decrypt cookies (owner headed login). Helper: `scripts/home-headed-login.sh naukri` |

## Fixed for 2026-08-11 Instahyre home (Windows residential)

| Issue | Fix |
| --- | --- |
| `tools/instahyre/resume.js` only searched `/workspace` + `/home/ubuntu` | Resolve `resumes/Rafi_Resume.docx` from repo/cwd and reuse `chrome_session` `PROFILES.instahyre` |
| Cookie-name `sessionid` present but live page redirects to `/login/` (`sessionLen=0`) | Same Chrome **v20 ABE** as Naukri — owner headed login via `scripts/home-headed-login.sh instahyre` |
| Home daily stopped with `destHasAuth: false` / no live probe parity with Cutshort | Added `tools/instahyre/wait_for_cdp_login.js` + wired into `scripts/home-headed-login.sh` |

## Still requires your action (cannot fix from code alone)

| Blocker | Who | What to do |
| --- | --- | --- |
| Windows `agent worker start` ABI crash (127/137) | You | Until Cursor ships a fixed Win package: `wsl --install -d Ubuntu` → `powershell -ExecutionPolicy Bypass -File scripts\fix-windows-agent-worker.ps1 -LaunchWsl` (or `bash scripts/setup-wsl-agent-worker.sh --name job-apply-laptop` inside WSL). Leave WSL terminal open; pick that machine in Agents. |
| Windows home portal CDP login (ABE v20) | You | One-time: `bash scripts/home-headed-login.sh instahyre` (also naukri/linkedin/foundit/cutshort/indeed). Sign in in the headed window; do **not** rely on Desktop Default cookie sync. |
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
