# Issues from last cron + fixes

## Fixed in this repo

| Issue | Fix |
| --- | --- |
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

## Still requires your action (cannot fix from code alone)

| Blocker | Who | What to do |
| --- | --- | --- |
| Snapshot missing portal logins | You | `bash scripts/open-portal-login-tabs.sh` → sign in on Desktop → quit Chrome → `bash scripts/verify-portal-logins.sh --strict` → **Save/Update snapshot** |
| Indeed Cloudflare 403 on datacenter IP | You | Run Indeed on **home Wi‑Fi** / private residential worker, **or** set secret `INDEED_HTTP_PROXY` (see `automation-prompts/INDEED_CLOUDFLARE.md`) |
| Hirist secondary board login | Optional | Log into Hirist in Desktop Chrome and re-seed sessions if you want Hirist applies |
| Workday / Greenhouse OTP ATS walls | Optional | Keep Gmail logged in same Chrome profile; complete OTP once per ATS |
| Verified notification sender missing | You | Set secret `RESEND_FROM_EMAIL` to a verified sender; fallback uses `Job Status <onboarding@resend.dev>` |
| General Daily duplicate | You | Keep disabled: https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441 |
| Indeed home results → daily mail | You | Keep home cron on; ensure home PC can `git push origin automation-results`; re-paste Notification loader from `ONE_TIME_LOADERS.md` once |

## After merging this PR

1. Re-paste updated prompts from `automation-prompts/0*.md` into each automation (resume section changed).
2. Merge to `main` (or point automations at this branch) so cron checkouts include `resumes/Rafi_Resume.docx`.
3. Complete portal logins + snapshot once.
4. For Indeed: enable private worker.
5. For Notification: connect Resend MCP + `RESEND_FROM_EMAIL`.
