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

## Daily automation readiness

Before saving a daily automation snapshot, log into each portal in Desktop Chrome
Default, then run:

```bash
bash scripts/sync-chrome-sessions.sh --strict
node tools/chrome_session.js status
```

Disable the duplicate General Daily automation
`30e2c023-9067-11f1-ba66-0e7d0216e441`; Naukri Daily owns that flow.
