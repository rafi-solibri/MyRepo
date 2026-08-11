# MyRepo

Job-apply automation assets for Mohammed Abdul Rafi Ahmed.

## Resume

Canonical file: [`resumes/Rafi_Resume.docx`](resumes/Rafi_Resume.docx)

```bash
bash scripts/bootstrap-job-assets.sh
```

## Agent instructions

See [`automation-prompts/README.md`](automation-prompts/README.md).

Shared targets: **Expected CTC 65 LPA**, **Hyderabad + Remote/WFH**, **Rafi_Resume.docx**, company-website/ATS completion (not Easy Apply only).

Issue log: [`automation-prompts/ISSUES_AND_FIXES.md`](automation-prompts/ISSUES_AND_FIXES.md).

## Portal login (required for daily cron)

If automations stop at Sign-in pages, the saved environment snapshot is missing auth cookies.

```bash
bash scripts/open-portal-login-tabs.sh          # Desktop Chrome tabs
bash scripts/verify-portal-logins.sh --strict   # must show all 6 OK
```

Then **Save / Update snapshot** on the environment dashboard. Details: [`automation-prompts/ENV_READINESS.md`](automation-prompts/ENV_READINESS.md).

## Daily automation readiness

Before saving a daily automation snapshot, log into each portal in Desktop Chrome
Default, then run:

```bash
bash scripts/sync-chrome-sessions.sh --strict
node tools/chrome_session.js status
```

Disable the duplicate General Daily automation
`30e2c023-9067-11f1-ba66-0e7d0216e441`; Naukri Daily owns that flow.

## Home-local evening replicas (cloud can stay ON)

Second daily pass at **5 PM** on this PC (Task Scheduler + Cursor CLI). Cloud
morning automations can remain enabled.

See [`automation-prompts/HOME_AUTOMATIONS.md`](automation-prompts/HOME_AUTOMATIONS.md).

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-all-home-tasks.ps1
```
