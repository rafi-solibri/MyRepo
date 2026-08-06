# Environment readiness for 6 daily job automations

## Verdict (checked from cloud agent)

| Item | Status |
| --- | --- |
| PR #8 merged to `main` (resume + helpers) | YES |
| Environment exists | YES — [545c2557-9097-11f1-ba66-0e7d0216e441](https://cursor.com/dashboard/cloud-agents/environments/e/545c2557-9097-11f1-ba66-0e7d0216e441) |
| Successful environment builds exist | YES (older snapshots) |
| **Saved snapshot with portal logins** | **NO** — cold boots; Naukri/Foundit/Instahyre/Indeed have 0 cookies |
| LinkedIn auth (`li_at`) in snapshot | **NO** — only marketing cookies |
| Cutshort auth cookie present on this VM | Partial (`cutshort_authentication`) — not guaranteed on next cold boot |
| Resume file in git | YES — `resumes/Rafi_Resume.docx` |
| Indeed Cloudflare / private worker | **NO** — managed cloud IP will keep failing |

**Conclusion:** Save Environment is **not** complete for unattended 9 AM runs. Automations are enabled, but most will stop at login (and Indeed at Cloudflare) until you finish the steps below.

## What you must do once (Desktop)

1. Open Cloud Agent Desktop / Take control for this environment.
2. In Chrome (non-default profile dirs are fine), log in to:
   - LinkedIn
   - Naukri (+ Gmail if OTP)
   - Foundit
   - Cutshort
   - Instahyre
   - Indeed (prefer **private worker** / residential IP)
3. Confirm each site shows your logged-in home/profile (not Sign in).
4. Open [Environment dashboard](https://cursor.com/dashboard/cloud-agents/environments/e/545c2557-9097-11f1-ba66-0e7d0216e441) → **Save / Update snapshot** (or Save after install) so those Chrome sessions persist for cron.
5. Paste one-time loaders from `ONE_TIME_LOADERS.md` if you have not already.
6. For notification email: authenticate Resend MCP + set `RESEND_FROM_EMAIL`.

Until step 4 is done, daily runs will keep hitting login walls on cold VMs.
