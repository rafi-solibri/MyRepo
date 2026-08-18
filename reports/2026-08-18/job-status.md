# Job status — 2026-08-18 (post-fix re-run)

Post-fix 11 AM status job on merged `main` (`d756d55` / PR #210).
Report run: https://cursor.com/agents/bc-1620c504-c327-43cc-b40c-cfb8f67180d1
Earlier 10:04 IST mail (0 applies, before ensure-missing launch): https://cursor.com/agents/bc-f595cdd4-cda0-4d5e-a5c7-748726b2a8c0
Targets: Expected CTC 65 LPA; Hyderabad + Remote/WFH; resume `Rafi_Resume.docx`.
From: `Job Status <onboarding@resend.dev>` (`RESEND_FROM_EMAIL` unset — owner: set a verified sender).

**Totals today (known, not invented):** applied 0 · external 0 · rejected 0 · blocked 0 · skipped 0.

9 AM apply crons were **enabled** but produced **no morning agents**. Home-local same-day JSON is missing for every portal. After PR #210 merged, the earlier 11 AM status run launched cron-miss recovery agents (~11:00 IST). Those jobs are still **RUNNING**; combined applies remain 0 at send. This re-run did **not** launch more agents (LinkedIn already at the 5/day post-fix cap).

## Portal results

| Portal | Home same-day | Applied | External | Rejected | Blocked | Skipped | Seen | Cloud today |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| LinkedIn | missing (latest home 2026-08-11) | 0 | 0 | 0 | — | — | — | 5 post-fix agents RUNNING (cap) |
| Foundit | missing (latest home 2026-08-15) | 0 | 0 | 0 | — | — | — | 1 post-fix agent RUNNING |
| Cutshort | missing (latest home 2026-08-16) | 0 | 0 | 0 | — | — | — | 1 post-fix agent RUNNING |
| Naukri | missing (latest home 2026-08-16) | 0 | 0 | 0 | — | — | — | 1 post-fix agent RUNNING |
| Instahyre | missing (latest home 2026-08-15) | 0 | 0 | 0 | — | — | — | 1 post-fix agent RUNNING |
| Indeed | missing (latest home 2026-08-15) | 0 | 0 | 0 | — | — | — | 1 post-fix agent RUNNING |
| Hitech City | missing + `hitechcity-daily.json` ABSENT (latest home 2026-08-15) | 0 | 0 | 0 | — | — | — | 1 post-fix agent RUNNING |

Stale home JSON was **not** counted as today’s applies. Portal session seeds in this environment look present (`portal-login-status.json` destHasAuth true for linkedin/naukri/foundit/cutshort/instahyre/indeed).

### Home fetch notes (not today’s counts)

- LinkedIn latest home 2026-08-11: applied 0 / blocked 12 / skipped 6 — Easy Apply daily limit; `no_same_day_home_result_for_2026-08-18`
- Foundit latest home 2026-08-15: applied 0 / skipped 1186
- Cutshort latest home 2026-08-16: applied 0 / blocked 1 — `agent_finished_without_same_day_report_exit_0`
- Naukri latest home 2026-08-16: applied 0 / blocked 1 — `agent_finished_without_same_day_report_exit_0`
- Instahyre latest home 2026-08-15: applied 0 / skipped 677 / seen 677
- Indeed latest home 2026-08-15: applied 0 / blocked 1 — `indeed_cloudflare_private_worker_required` (not treated as today)
- Hitech City latest home 2026-08-15: applied 0 / blocked 32 / skipped 732 — CDP/captcha/board preflight

## Cron-miss recovery (launched, still running)

`bash scripts/ensure-missing-daily-runs.sh` was already executed by the earlier 11 AM status run after PR #210. This post-fix re-run did **not** re-launch (agents exist; LinkedIn at 5/day cap).

| Portal | Agent | Status |
| --- | --- | --- |
| Foundit | https://cursor.com/agents/bc-27da46d8-1b15-456b-9d12-e027be995dfd | RUNNING |
| Cutshort | https://cursor.com/agents/bc-926e0851-c2db-4b08-a140-40df2bfac153 | RUNNING |
| Naukri | https://cursor.com/agents/bc-5b599d15-db8d-448b-b227-47acc49fce69 | RUNNING |
| Instahyre | https://cursor.com/agents/bc-2a3d1def-a579-4ced-af49-e47517e88000 | RUNNING |
| Indeed | https://cursor.com/agents/bc-006ce3d6-107f-4a4f-b4b3-a4ef45f030a0 | RUNNING |
| Hitech City | https://cursor.com/agents/bc-e2fc2f81-1a8c-4430-9730-273532b76351 | RUNNING |
| LinkedIn (1/5) | https://cursor.com/agents/bc-c9695855-9b8b-470d-8800-83052913d93d | RUNNING |
| LinkedIn (2/5) | https://cursor.com/agents/bc-1cf5416a-34d5-4cf3-b0fc-e9e0f0732ae6 | RUNNING |
| LinkedIn (3/5) | https://cursor.com/agents/bc-6297d74c-1baa-4c9b-a85e-0e636ba68d40 | RUNNING |
| LinkedIn (4/5) | https://cursor.com/agents/bc-fa97c68f-ce27-4e58-8c4b-e5f582cfe5fe | RUNNING |
| LinkedIn (5/5) | https://cursor.com/agents/bc-f87e1b4e-b398-4f8d-ae66-5c5eeebe178c | RUNNING |

Five LinkedIn agents are leftover from pre-#210 non-exclusive `--portal` re-runs (the bug #210 fixed). No further LinkedIn post-fix re-runs today.

## Owner actions (not code-fixable)

1. Confirm why LinkedIn/Foundit/Cutshort/Naukri/Instahyre/Indeed/Hitech City **9 AM IST crons did not fire** on 2026-08-18 (schedule / quota / UI). Automations are enabled.
2. Create/enable the separate **Ensure Missing Daily Runs** automation (~10:30 AM IST) per `automation-prompts/09-ensure-missing.md` / `ONE_TIME_LOADERS.md` so mid-morning recovery does not depend on the 11 AM status job.
3. Set `RESEND_FROM_EMAIL` to a verified domain sender (currently `Job Status <onboarding@resend.dev>`).
4. Evening home-local replicas still needed for residential IP (Indeed Cloudflare historically requires this).
5. Do not start more LinkedIn post-fix re-runs today (already at cap 5).

## Fix PRs

Merged 2026-08-18 IST:

- https://github.com/rafi-solibri/MyRepo/pull/210 — fix: exclusive `--portal` re-runs + cron-miss `ensure-missing-daily-runs.sh` from the 11 AM status job

Merged 2026-08-17 (context only, not today’s apply totals):

- #209 LinkedIn primary-location filter / SoC skip / 999 backoff
- #208 ATS `import os` in persist_retry
- #207 Indeed SmartApply notice days=0 and Country/+91 combobox
- #206 Hitech City honor `OWNER_ASLEEP` short ATS waits
- #205 Naukri skip Pega/LSA, AI EM, Data/GCP Infra

Open (older / drafts): #200, #153, #150, #134, #93.

## Status-mail pipeline

- Home fetches: `bash scripts/fetch-home-result.sh <portal> --today` for linkedin/foundit/cutshort/naukri/instahyre/indeed/hitechcity — all `sameDay: false`.
- Resend MCP used (Resend ready). `RESEND_API_KEY` unset in this env; MCP send does not need it.
- Earlier mail `ed785235-11c8-49b3-8449-84c9cfd9c902` at 04:34 UTC reported the cron miss **before** ensure-missing launched.
- This post-fix mail: `35c00590-b32d-4d21-b05f-43f9bdbf5d9d` (subject `Job status — 2026-08-18 (post-fix re-run)`).
- No new code-fixable mail-pipeline bug on this re-run; did not launch another 11 AM status post-fix loop.
