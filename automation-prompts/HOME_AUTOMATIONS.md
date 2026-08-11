# Home-local automation replicas (evening — cloud stays ON)

Cursor **cloud Automations** can keep running in the morning. These **home PC
replicas** run in the evening on your residential IP + local Chrome logins via:

1. Windows Task Scheduler
2. Cursor CLI (`agent`) on this machine
3. Same prompts as cloud (`automation-prompts/0*.md`)

## What gets installed

| Scheduled task | Default time (local) | Script |
| --- | --- | --- |
| HomeDaily-LinkedIn | 17:00 | `portal-home-daily.sh linkedin` |
| HomeDaily-Foundit | 17:20 | `portal-home-daily.sh foundit` |
| HomeDaily-Cutshort | 17:40 | `portal-home-daily.sh cutshort` |
| HomeDaily-Naukri | 18:00 | `portal-home-daily.sh naukri` |
| HomeDaily-Instahyre | 18:20 | `portal-home-daily.sh instahyre` |
| HomeDaily-Indeed | 18:40 | `portal-home-daily.sh indeed` |
| HomeDaily-Notification | 19:30 | `notification-home-daily.sh` |

Stagger avoids 6 Chrome/CDP sessions fighting (all portals share CDP `:9222` — run one at a time).

## One-time setup (this PC)

```powershell
# 1) Cursor CLI
irm 'https://cursor.com/install?win32=true' | iex
agent login
# Optional unattended: set user env CURSOR_API_KEY from https://cursor.com/dashboard/api

# 2) Repo
cd C:\Users\MohammedAhmed\MyRepo
git checkout main
git pull

# 3) Git for Windows (Git Bash) — required by the scheduled tasks

# 4) Install all daily tasks (5 PM start by default)
powershell -ExecutionPolicy Bypass -File scripts\install-all-home-tasks.ps1
```

Custom times:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-all-home-tasks.ps1 `
  -BaseTime "17:00" -StaggerMinutes 20 -NotificationTime "19:30"
```

## Run all portals now (sequential)

```powershell
& "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe" scripts/run-all-home-now.sh
```

## Test one portal

```powershell
& "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe" scripts/portal-home-daily.sh linkedin
```

Logs: `~/.cursor/portal-home-logs/<portal>/`  
JSON: `artifacts/<portal>-daily-run.json` (also published to git branch `automation-results`)

## Keep PC awake

Task Scheduler cannot run if the machine is asleep. Use:

- Windows → Power → never sleep on AC (or schedule wake)
- Or run a portal manually when you are at the desk

## Cloud + local together

Leave cloud automations **On**. Local evening runs are a second pass — already-applied
roles should be skipped. Do not turn cloud off unless you want local-only.

## Portal login on this PC

Home runs use **per-portal CDP profiles** under
`%USERPROFILE%\.cursor\chrome-cdp-profiles\<portal>` — not a copy of Desktop Chrome.

Chrome 127+ **App-Bound Encryption** prevents copying cookies from Desktop Default into
another `--user-data-dir`. Do this once per portal:

1. Close all Chrome windows.
2. `bash scripts/launch-chrome-cdp.sh linkedin` (headed).
3. Sign into LinkedIn in that window; leave the profile logged in.
4. Repeat for foundit / cutshort / naukri / instahyre / indeed.
5. Re-run `bash scripts/preflight-portal-run.sh <portal>` — it should report `destHasAuth: true`.

Do **not** rely on Desktop Default cookie sync on Windows for CDP automation.

## Notification email

`HomeDaily-Notification` loads each portal’s same-day JSON via
`scripts/fetch-home-result.sh <portal> --today`, then emails
`rafi.success@gmail.com` (Resend MCP or `RESEND_API_KEY`).

## Uninstall

```powershell
Get-ScheduledTask HomeDaily-* | Unregister-ScheduledTask -Confirm:$false
Unregister-ScheduledTask -TaskName IndeedHomeDaily -Confirm:$false
```
