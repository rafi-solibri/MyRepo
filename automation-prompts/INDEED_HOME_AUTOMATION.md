# Indeed home automation (free — no Cursor cloud Automation)

Cursor **dashboard Automations cannot be created by this agent** (API is
read-only), and on individual plans they also **cannot** use your home IP.

This repo instead ships a **home-machine schedule** that runs Indeed on your
residential network.

## One-time setup (home PC, home Wi‑Fi)

```bash
# 1) Install Cursor CLI + login
curl https://cursor.com/install -fsS | bash   # Windows: irm 'https://cursor.com/install?win32=true' | iex
agent login

# 2) Repo on main
cd /path/to/MyRepo
git checkout main && git pull

# 3) Optional but recommended for unattended cron: API key
#    https://cursor.com/dashboard/api → create Personal API key
#    export CURSOR_API_KEY=...   (add to ~/.bashrc / Windows env)
```

## Install the daily schedule

**macOS / Linux / WSL** (09:00 local by default):

```bash
bash scripts/install-indeed-home-cron.sh 09:00
```

**Windows** (PowerShell):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-indeed-home-task.ps1 -Time 09:00
```

## Test immediately

```bash
bash scripts/indeed-home-daily.sh
```

Logs: `~/.cursor/indeed-home-logs/`

After each run the script normalizes `artifacts/indeed-daily-run.json` and
**publishes** it to git branch `automation-results` (`automation-results/indeed/YYYY-MM-DD.json`
+ `latest.json`) so the 11 AM Notification Job can include applied / rejected /
blocked / skipped counts in the daily mail.

```bash
bash scripts/publish-indeed-home-result.sh   # re-publish last report if needed
bash scripts/fetch-indeed-home-result.sh --today   # what Notification Job reads
```

Home machine must be able to `git push origin automation-results` (same GitHub
auth you use for this repo).

## Also do this in the Cursor UI

1. Cloud Indeed often hits Cloudflare on public IPs — home evening Indeed is the reliable pass.  
   Cloud Indeed may stay On if you want; expect Cloudflare stubs there.  
2. Install **all** home replicas (5 PM stagger):  
   see [HOME_AUTOMATIONS.md](HOME_AUTOMATIONS.md) / `scripts/install-all-home-tasks.ps1`  
3. Other portal cloud automations can stay On (morning); home is an evening second pass.

## If you still want a Cursor dashboard Automation

You can create one manually at https://cursor.com/automations → New:

| Field | Value |
| --- | --- |
| Name | Indeed Home Reminder (optional) |
| Schedule | Daily 9 AM |
| Prompt | See below |

But on public cloud it will **still fail** Cloudflare unless you add a paid
`INDEED_HTTP_PROXY`. Prefer the home cron above.

```text
Indeed cannot run on Cursor public cloud (Cloudflare Request Blocked).
If this run is on a home/residential worker, execute automation-prompts/06-indeed.md.
Otherwise exit and remind: run `bash scripts/indeed-home-daily.sh` on the home PC.
```
