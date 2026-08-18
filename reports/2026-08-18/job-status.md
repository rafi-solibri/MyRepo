# Job status — 2026-08-18

11 AM status job **post-fix re-run #2** after merged [PR #211](https://github.com/rafi-solibri/MyRepo/pull/211) (Ensure Missing via GitHub Actions).
This run: https://cursor.com/agents/bc-cbc1ef94-0da7-4cc1-94c1-7259bfd1c484
Earlier 10:04 IST mail (0 applies, before ensure-missing): https://cursor.com/agents/bc-f595cdd4-cda0-4d5e-a5c7-748726b2a8c0
First post-fix mail (0 applies, agents still starting): https://cursor.com/agents/bc-1620c504-c327-43cc-b40c-cfb8f67180d1

Targets: Expected CTC 65 LPA; Hyderabad + Remote/WFH; resume `Rafi_Resume.docx`.
From: `Job Status <onboarding@resend.dev>` (`RESEND_FROM_EMAIL` unset — owner: set a verified sender).

**Combined known applies today: 10** (Foundit 6 + Instahyre 2 + Cutshort 2). Nothing invented. Yesterday's LinkedIn 21 Easy Applies are **not** counted.

## Totals (2026-08-18 known)

Applied **10** · External **0** completed · Rejected **2** (Indeed so far) · Blocked **15+** · Skipped **1883+** · Seen **736+**

Naukri still has **no same-day report** (helper running). Cutshort / Indeed / Hitech still RUNNING at send time; their counts are last confirmed snapshots.

## Portal results

Home-local same-day JSON is **missing** for every portal (`no_same_day_home_result_for_2026-08-18`). Stale home dates: LinkedIn 2026-08-11, Foundit/Instahyre/Indeed/Hitech 2026-08-15, Cutshort/Naukri 2026-08-16. Those stale counts are **not** today's applies.

Source for today: cloud post-fix agents launched by `ensure-missing-daily-runs.sh` after PR #210/#211 (~11:00 IST).

| Portal | Home today | Applied | External | Rejected | Blocked | Skipped | Seen | Cloud status | Blocker |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| LinkedIn | missing (latest 2026-08-11) | 0 | 0 | 0 | 1 | 0 | 0 | IDLE (5/5 post-fix cap) | Account temporarily restricted until **2026-08-18 9:09 PM PDT** / CAPTCHA checkpoint. Owner-only. |
| Foundit | missing (latest 2026-08-15) | 6 | 0 done | — | 0 | 1188 | — | IDLE | Login OK. Applied tab 490→497. SoC/RTL false apply + event ATS timeout noted. |
| Cutshort | missing (latest 2026-08-16) | 2 | — | — | — | (scan filters) | 3190 scanned | RUNNING | Login OK. Questionnaire pass still in progress. |
| Naukri | missing (latest 2026-08-16) | — | — | — | — | — | — | RUNNING | No `naukri-daily-apply.json` yet. Profile refreshed. Accenture SSO tab leak. |
| Instahyre | missing (latest 2026-08-15) | 2 | 0 | — | 0 | 674 | 676 | IDLE | Login OK. No OTP/Cloudflare. |
| Indeed | missing (latest 2026-08-15 Cloudflare; **not used as today**) | 0 | 0 | 2 | 6 | 15 | 24 | RUNNING | WARP+UC + session OK. External ATS timeouts / no form. |
| Hitech City | missing | 0 | — | — | 8 | 18 | 26 | RUNNING (2nd careers pass) | First pass 0 submits. JPMC/Experian CAPTCHA, ModMed login, Oracle timeout. |

`automation-results/<portal>/2026-08-18.json`: **absent** for all portals.

## Highlights (confirmed applies only)

**Instahyre** (finished): 2 in-app `application_sent`
- Snap — Azure / .NET Developer (job 438811)
- D. E. Shaw — Backend Engineer (job 438809)

**Foundit** (finished, `daily_apply.js` EXIT 0): 6 intentional applies; Applied tab 490→497
- CareerXperts Consulting — Senior Dotnet Developer (63072569)
- Globallogic Ukraine — Senior .NET Lead (63102686) — `linkedin_no_easy_apply`
- Jobgether — Senior Integration Developer/Architect (63068789) — `linkedin_no_easy_apply`
- Accenture — Technology Architect (63129958) — `external_incomplete_or_timeout`
- tylsemi — Principal Engineer - SoC RTL Design (63126832) — false apply (silicon/RTL); `linkedin_login_wall`
- locaxion — Senior Software Architect (42224019) — `linkedin_no_easy_apply`

**Cutshort** (still running; 2 confirmed `=> applied`):
- Principal Enterprise GenAI / Agentic AI Architect @ Ampera Technologies (40 LPA)
- Power BI Solution Architect @ Wehyb Online Services LLP (35 LPA)
- scanned=3190, qualifying=2

**LinkedIn:** 0 applies. Five leftover post-fix agents (pre-#210 exclusive-`--portal` bug) all blocked at login (CAPTCHA or account restriction until 9:09 PM PDT). Do not launch more LinkedIn re-runs today (cap 5).

**Indeed:** 0 applied / 0 external completed so far; 24 seen. Cloudflare cleared on this cloud run (WARP+UC). Not using 2026-08-15 home Cloudflare result.

**Hitech City:** first careers-only pass 0 applied (8 blocked / 18 skipped / 26 seen). Agent patched Oracle Hyd-title skip on a feature branch (PR create 403) and started a second pass — still 0 confirmation submits at send time.

**Naukri:** helper running; no counts to report.

## Cron-miss / recovery

9 AM apply automations are **enabled** but produced **zero** morning agents on 2026-08-18. Ensure Missing Cursor Automation is still **absent** (API cannot create it).

Recovery already ran (do **not** re-launch):
1. PR #210 — exclusive `--portal` re-runs + 11 AM cron-miss `ensure-missing-daily-runs.sh`
2. `bash scripts/ensure-missing-daily-runs.sh` launched all seven apply portals (~11:00 IST)
3. PR #211 — GitHub Actions workflow **Ensure Missing Daily Runs** (cron `0 5 * * *` = 10:30 IST)

This 11 AM status re-run did **not** call ensure-missing again and did **not** launch more portal agents.

### Apply agent URLs

Finished:
- Instahyre: https://cursor.com/agents/bc-2a3d1def-a579-4ced-af49-e47517e88000
- Foundit: https://cursor.com/agents/bc-27da46d8-1b15-456b-9d12-e027be995dfd
- LinkedIn (5, all 0 applies): https://cursor.com/agents/bc-c9695855-9b8b-470d-8800-83052913d93d · https://cursor.com/agents/bc-1cf5416a-34d5-4cf3-b0fc-e9e0f0732ae6 · https://cursor.com/agents/bc-6297d74c-1baa-4c9b-a85e-0e636ba68d40 · https://cursor.com/agents/bc-fa97c68f-ce27-4e58-8c4b-e5f582cfe5fe · https://cursor.com/agents/bc-f87e1b4e-b398-4f8d-ae66-5c5eeebe178c

Still running at send:
- Cutshort: https://cursor.com/agents/bc-926e0851-c2db-4b08-a140-40df2bfac153
- Naukri: https://cursor.com/agents/bc-5b599d15-db8d-448b-b227-47acc49fce69
- Indeed: https://cursor.com/agents/bc-006ce3d6-107f-4a4f-b4b3-a4ef45f030a0
- Hitech City: https://cursor.com/agents/bc-e2fc2f81-1a8c-4430-9730-273532b76351

## Owner actions (not code-fixable)

1. Confirm why 9 AM apply crons did not fire 2026-08-18 (schedule / quota / UI). Automations are enabled.
2. Paste/enable the Cursor **Ensure Missing Daily Runs** automation (~10:30 AM IST) per `automation-prompts/09-ensure-missing.md` (GHA backup is now on main via #211; still needs repo secret `CURSOR_API_KEY`).
3. LinkedIn: wait for restriction lift (9:09 PM PDT) and/or clear Security Verification in headed Chrome. Do not start more LinkedIn post-fix re-runs today (cap 5).
4. Set `RESEND_FROM_EMAIL` to a verified domain sender.
5. Evening home-local replicas still useful for residential IP.
6. Foundit/Hitech agents hit GitHub 403 when opening fix PRs — owner may need to open those from pushed branches.

## Fix PRs today (merged)

- https://github.com/rafi-solibri/MyRepo/pull/211 — schedule Ensure Missing via GitHub Actions
- https://github.com/rafi-solibri/MyRepo/pull/210 — exclusive `--portal` re-runs + cron-miss ensure-missing

Open older (unrelated): #200, #153, #150, #134, #93.

Portal apply agents pushed login/filter branches today but **did not merge PRs** (GitHub App 403 / approval queue).

## Status-mail pipeline

- Resend MCP: available
- Home fetch: `bash scripts/fetch-home-result.sh <portal> --today` for linkedin, foundit, cutshort, naukri, instahyre, indeed, hitechcity — all stale / not same-day
- `RESEND_API_KEY` unset in this session (MCP used instead)
- `RESEND_FROM_EMAIL` unset — fallback `Job Status <onboarding@resend.dev>`
- This email: Resend id `9d831a87-fd45-4312-a491-a8012974c0a0`
- Earlier emails today: `ed785235-11c8-49b3-8449-84c9cfd9c902` (morning 0 applies), `35c00590-b32d-4d21-b05f-43f9bdbf5d9d` (first post-fix, agents still starting)
