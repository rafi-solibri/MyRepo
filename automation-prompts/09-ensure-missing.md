# Ensure-missing / mid-morning recovery (10:30 AM IST)

```text
You recover daily job-apply portals that did not produce a usable same-day result.

1) Read and OBEY automation-prompts/AUTO_FIX.md and automation-prompts/MAX_APPLY_OWNER_CHECKLIST.md (owner blockers stay owner-only).
2) Run: `bash scripts/ensure-missing-daily-runs.sh`
   - Optional dry-run first: `bash scripts/ensure-missing-daily-runs.sh --dry-run`
3) This launches only portals missing usable coverage (login-wall / 0-seen / cron-did-not-fire do NOT count as done).
4) Prefer fresh cloud agents when `CURSOR_API_KEY` is set; otherwise same-session durable apply scripts.
5) Cap: each portal is still subject to post-fix re-run max 5/IST day.
6) Report which portals were launched, applied counts, and any login_required owner actions.
7) Do NOT invent applies. Do NOT force-restore portal session seeds over live auth (`FORCE_RESTORE_SESSIONS` must stay unset/0 unless the owner explicitly asked).
```

## Schedule (owner pastes once)

Create a Cursor Automation named **Ensure Missing Daily Runs** scheduled **~10:30 AM IST** (after the 9 AM portal wave, before Notification at 11 AM).

Paste the fenced `text` block above as the Agent instruction (or use the short loader in `ONE_TIME_LOADERS.md`).

Requires environment secret **`CURSOR_API_KEY`** so missing portals can launch as fresh cloud jobs on `main`.

### Durable backup (no Automations UI required)

GitHub Actions workflow **Ensure Missing Daily Runs** (`.github/workflows/ensure-missing-daily.yml`) runs `bash scripts/ensure-missing-daily-runs.sh` on cron `0 5 * * *` (10:30 AM IST) and via `workflow_dispatch`. Needs repo secret `CURSOR_API_KEY`. Agents cannot create Cursor Automations via API — prefer the UI automation above; keep this workflow enabled as backup.
