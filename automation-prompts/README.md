# Job-apply automation prompts (refined)

Paste each file’s fenced `text` block into the matching Cursor Automation **Agent instructions**, then Save.

## Shared targets

| Rule | Value |
| --- | --- |
| Resume | **`resumes/Rafi_Resume.docx`** (bootstrap copies to Documents/resumes) |
| Expected CTC | **65 LPA** |
| Current CTC | **52 LPA** |
| Locations | Hyderabad / Telangana **or** Remote / WFH |
| Apply paths | Easy/Quick Apply **and** company website / ATS |

## First command every run

```bash
bash scripts/bootstrap-job-assets.sh
python3 tools/resume_paths.py
```

## Automations

| Automation | Prompt |
| --- | --- |
| LinkedIn Daily 9 AM | [01-linkedin.md](01-linkedin.md) |
| Foundit Daily 9 AM | [02-foundit.md](02-foundit.md) |
| Cutshort Daily 9 AM | [03-cutshort.md](03-cutshort.md) |
| Naukri Daily 9 AM | [04-naukri-general.md](04-naukri-general.md) |
| Instahyre Daily 9 AM | [05-instahyre.md](05-instahyre.md) |
| Indeed Daily 9 AM | [06-indeed.md](06-indeed.md) |
| Notification Job 11 AM | [07-notification.md](07-notification.md) |

See [ISSUES_AND_FIXES.md](ISSUES_AND_FIXES.md) for what was broken in the last cron and what still needs your login/secrets.
