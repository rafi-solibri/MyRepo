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

## Also do this in the Cursor UI

1. **Disable** the cloud Indeed Daily automation (it hits Cloudflare):  
   https://cursor.com/automations/91b09fd7-9093-11f1-ba66-0e7d0216e441 → Off  
2. Keep LinkedIn / Naukri / Foundit / Cutshort / Instahyre cloud automations On.

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
