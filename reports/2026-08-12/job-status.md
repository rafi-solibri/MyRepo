# Job status — 2026-08-12

Home-local Notification Job on `NEM01-GBGR234` (residential Windows), evening run ~19:20 IST.
Targets: Expected CTC 65 LPA; Hyderabad + Remote/WFH; resume `Rafi_Resume.docx`.

**Totals today:** applied 1 · external 0 · rejected 1 · blocked 25 · skipped 3286 across LinkedIn, Foundit, Cutshort, Naukri, Instahyre, Indeed, Hitech City.

## Portal results (source: home-local, same-day)

| Portal | Applied | External | Rejected | Blocked | Skipped | Seen | OK | Blocker |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| LinkedIn | 0 | 0 | 0 | 1 | 0 | 0 | no | Security Verification / CAPTCHA — owner headed login required |
| Foundit | 0 | 0 | 0 | 1 | 0 | 0 | no | `foundit_login_required` — `bash scripts/home-headed-login.sh foundit` |
| Cutshort | 0 | 0 | 1 | 0 | 0 | 1929 | no | Logged in; qualifying=0; `q_locked_empty=322` (questionnaire_locked_empty) |
| Naukri | 0 | 0 | 0 | 9 | 2604 | 291 | no | `external_incomplete_or_timeout` (profile updated today; live CDP after SQLite lock) |
| Instahyre | 1 | 0 | 0 | 0 | 675 | 676 | yes | — |
| Indeed | 0 | 0 | 0 | 1 | 0 | 0 | no | `indeed_cloudflare_private_worker_required` |
| Hitech City / Knowledge City | 0 | 0 | 0 | 13 | 7 | 37 | no | LinkedIn Security Verification (no li_at); careers: Amazon passport + Palo Alto/Qualcomm CAPTCHA |

Finished timestamps (UTC): Foundit 11:57 · LinkedIn 11:59 · Cutshort 12:24 · Instahyre 12:54 · Naukri 12:59 · Indeed 13:12 · Hitech City 13:43.

`automation-results/<portal>/YYYY-MM-DD.json` dates: all same-day `2026-08-12` (home-local).

## Highlights

- Only successful apply: Instahyre — **Sr. Software Engineer @ Ansrsource (Hyderabad)** via Instahyre UI (`application_sent`). Live CDP session OK after cookie DB lock; 3 undecided opportunities skipped (non-Hyd); API rate-limited once.
- Cutshort scanned 1929 jobs but 0 qualifying; 322 questionnaire payloads locked empty → counted as rejected.
- Naukri STEP0 profile refresh OK; most volume skipped; 9 external ATS attempts timed out / incomplete.
- LinkedIn + Foundit still need owner headed CDP login (Security Verification / login wall).
- Hitech City LinkedIn referrals blocked on Security Verification; company careers hit Amazon passport walls and CAPTCHA on Palo Alto / Qualcomm (plus some scan nav errors).
- Indeed remains Cloudflare / private-worker blocked on home residential path.
- No invented applies; all seven portals had same-day home-local JSON.

## Owner actions (not code-fixable)

1. Headed CDP login: `bash scripts/home-headed-login.sh linkedin` (clear Security Verification), then `foundit`, and LinkedIn again before Hitech City referrals.
2. Indeed: residential / private-worker path for Cloudflare (beyond current home skip-WARP setup).
3. Optional: complete Amazon passport / CAPTCHA sessions for Hitech City careers if those employers matter.
4. `RESEND_FROM_EMAIL` is still the onboarding fallback (`Job Status <onboarding@resend.dev>`) — set a verified domain sender when ready.

## Fix PRs merged today (AUTO_FIX)

- https://github.com/rafi-solibri/MyRepo/pull/108 — fix(hitechcity): survive Windows cp1252 unicode job titles
- https://github.com/rafi-solibri/MyRepo/pull/107 — fix(hitechcity): accept hitechcity in home-headed-login alias
- https://github.com/rafi-solibri/MyRepo/pull/106 — fix(naukri): home live CDP waiter, Hirist soft-skip, SRE filter
- https://github.com/rafi-solibri/MyRepo/pull/105 — fix(cutshort): live CDP preflight when Windows cookies DB is locked
- https://github.com/rafi-solibri/MyRepo/pull/104 — fix(linkedin): preserve Security Verification tabs during login wait
- https://github.com/rafi-solibri/MyRepo/pull/103 — fix(foundit): live CDP login waiter for Windows home ABE sessions
- https://github.com/rafi-solibri/MyRepo/pull/101 — fix(hitechcity): CAPTCHA bail, EXT caps, LinkedIn throttle retry, loc filters
- https://github.com/rafi-solibri/MyRepo/pull/100 — fix(linkedin): restore search list after /jobs/view + HTTP nav retries
- https://github.com/rafi-solibri/MyRepo/pull/99 — fix(indeed): stop reCAPTCHA review hang + Review/privacy CTA handling
- https://github.com/rafi-solibri/MyRepo/pull/98 — fix(naukri): open Go to company site when Apply CTA is disabled
- https://github.com/rafi-solibri/MyRepo/pull/97 — fix(cutshort): match C#/.NET skills without broken word-boundaries
- https://github.com/rafi-solibri/MyRepo/pull/96 — fix(foundit): seniority title skips + Workday Apply Manually handoff
- https://github.com/rafi-solibri/MyRepo/pull/95 — fix(instahyre): sweep undecided opportunities before job_search
- https://github.com/rafi-solibri/MyRepo/pull/94 — fix(naukri): Workday post-create Sign In + reliable password entry
- https://github.com/rafi-solibri/MyRepo/pull/92 — fix(naukri): Workday Sign in with email + password policy
- https://github.com/rafi-solibri/MyRepo/pull/91 — fix(hitechcity): skip US Workday URLs and Amazon passport walls
- https://github.com/rafi-solibri/MyRepo/pull/89 — fix(hitechcity): harden careers location filter to top-card only
- https://github.com/rafi-solibri/MyRepo/pull/88 — fix(instahyre): skip ops admin and data specialist titles
- https://github.com/rafi-solibri/MyRepo/pull/87 — fix(foundit): harden confirmLogin against Hi Seeker race
- https://github.com/rafi-solibri/MyRepo/pull/86 — fix(hitechcity): chrome_session SyntaxError + resolve-python LOCALAPPDATA
- https://github.com/rafi-solibri/MyRepo/pull/85 — fix(naukri): tolerate unset LOCALAPPDATA in resolve-python
- https://github.com/rafi-solibri/MyRepo/pull/83 — fix(indeed): restore JS function checkPortal in chrome_session
- https://github.com/rafi-solibri/MyRepo/pull/82 — fix(instahyre): restore function checkPortal in chrome_session.js
- https://github.com/rafi-solibri/MyRepo/pull/81 — fix(linkedin): restore preflight checkPortal + resolve-python on Linux
- https://github.com/rafi-solibri/MyRepo/pull/80 — fix(cutshort): restore function checkPortal in chrome_session.js
- https://github.com/rafi-solibri/MyRepo/pull/79 — fix(foundit): restore JS function checkPortal in chrome_session

Also merged (docs): #102 job-status summary, #90 foundit daily report.

Open at send time: #84 closed as superseded by #85 (LOCALAPPDATA already on main); #93 docs cloud rerun (draft).

## Notification pipeline note

Resend MCP: not connected (no MCP servers in this session).
Email sent via `scripts/send-job-status-email.mjs` — id `4bb2d8df-8b70-4bef-811c-2f32bc7546c4`. From = `Job Status <onboarding@resend.dev>` (verified domain sender not configured). First attempt hit corp TLS issuer error; retried with insecure TLS.
`scripts/fetch-home-result.sh` succeeded for all seven portals on this run.
