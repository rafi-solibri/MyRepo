# Max-apply owner checklist (do these once, then cron maximizes volume)

Code recommendations for volume are in `main`. The items below **cannot** be completed by the cloud agent alone — they need your Desktop / secrets / Automations UI.

## 1) Refresh portal logins + Save environment snapshot

Without fresh cookies, LinkedIn / Cutshort / Indeed hit login walls and apply **0**.

```bash
# Open portal tabs in Desktop Chrome
bash scripts/open-portal-login-tabs.sh

# Or per-portal headed login (home):
bash scripts/home-headed-login.sh linkedin
bash scripts/home-headed-login.sh cutshort
bash scripts/home-headed-login.sh indeed
# Optional: foundit naukri instahyre if verify fails
```

Sign in until each dashboard/feed loads (not a Sign-in page). Quit Chrome fully, then:

```bash
bash scripts/verify-portal-logins.sh --strict
node tools/chrome_session.js status
```

All apply portals must show OK. Then **Save / Update snapshot** on the Cloud Agents environment:
https://cursor.com/dashboard/cloud-agents/environments/e/545c2557-9097-11f1-ba66-0e7d0216e441

Optional: refresh seed from live profiles:

```bash
bash scripts/refresh-portal-session-seed.sh linkedin
bash scripts/refresh-portal-session-seed.sh cutshort
bash scripts/refresh-portal-session-seed.sh indeed
```

## 2) Set environment secrets

| Secret | Why |
| --- | --- |
| `CURSOR_API_KEY` | Post-fix + ensure-missing can launch **fresh** same-day cloud jobs (max 5/portal/day). Without it, only in-session re-exec works. |
| `LINKEDIN_EMAIL` + `LINKEDIN_PASSWORD` | Auto-heal LinkedIn when CDP session expires (still may need CAPTCHA once). |
| `INDEED_HTTP_PROXY` (optional) | True residential proxy for cloud Indeed when home Wi‑Fi is unavailable. |
| `NAUKRI_WORKDAY_PASSWORD` (or `WORKDAY_PASSWORD` / `ATS_PASSWORD`) | One shared password for Workday Create Account / Sign In. Helpers alias whichever of these is set. 12+ chars with complexity. |
| `CAPSOLVER_API_KEY` / `TWOCAPTCHA_API_KEY` | **Optional.** Paid token solvers for unattended iCIMS hCaptcha. Skip these if you do not want to pay — use the headed home click below instead. |

Dashboard → Cloud Agent environment → Secrets / API keys: https://cursor.com/dashboard/api

## 3) Paste Automations loaders (once)

See `automation-prompts/ONE_TIME_LOADERS.md`. Especially paste:

- **Ensure Missing Daily Runs** (~10:30 AM IST) — recovers “cron did not fire”
- Confirm LinkedIn / Cutshort / Instahyre / Indeed / Hitech loaders point at the current `automation-prompts/0x-*.md` files

Cursor Automations API is **read-only** for agents — only you can create/edit schedules in the UI.

## 4) Career-portal hCaptcha = headed home click (free)

Cloud AWS IPs cannot pass Hyland iCIMS hCaptcha without a paid solver or a human click. You do **not** need CapSolver.

```bash
# On your home PC (visible Chrome). Helper fills email / I accept, then waits.
bash scripts/home-headed-careers-apply.sh
# Optional longer wait:
ATS_CAPTCHA_WAIT_SEC=420 bash scripts/home-headed-careers-apply.sh
```

When the checkbox / image challenge appears, click it. The helper continues the apply. One-time iCIMS “Log back in!” in Desktop Chrome + Save snapshot can also skip the widget later.

## 5) Indeed = home-first

Prefer the **18:40 IST** home task (`scripts/indeed-home-daily.sh`). Cloud Indeed is best-effort (CF + anonymous session). Keep home Task Scheduler installed via `scripts/install-all-home-tasks.ps1`.

## 6) Do not force-restore stale seeds

Never set `FORCE_RESTORE_SESSIONS=1` unless you intend to overwrite live CDP auth with `.portal-sessions/` seeds (that wiped Cutshort on 2026-08-14).

## Done when

```bash
bash scripts/verify-portal-logins.sh --strict   # all OK
bash scripts/ensure-missing-daily-runs.sh --dry-run  # only truly missing portals listed
```

After the next morning cron + 10:30 ensure-missing, Notification (11 AM) should show applies across portals that have inventory.
