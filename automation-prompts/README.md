# Job-apply automation prompts (refined)

**This cloud agent cannot write automation Agent instructions** (Automations API is read-only).

**Recommended:** paste the short loaders in [ONE_TIME_LOADERS.md](ONE_TIME_LOADERS.md) once. After that, merge PRs and agents pull the latest full prompts from these files automatically.

Alternatively, paste each file’s full fenced `text` block into the matching automation, then Save.

## Shared targets

| Rule | Value |
| --- | --- |
| Resume | **`resumes/Rafi_Resume_Technical_Architect.docx`** (bootstrap copies to Documents/resumes; legacy aliases kept) |
| Expected CTC | **65 LPA** |
| Current CTC | **52 LPA** |
| Locations | Hyderabad / Telangana **or** Remote / WFH |
| Apply paths | Easy/Quick Apply **and** company website / ATS |

## First command every run

```bash
bash scripts/preflight-portal-run.sh <portal>
```

Use one of: `linkedin`, `foundit`, `cutshort`, `naukri`, `instahyre`, `indeed`.
The preflight bootstraps the resume, syncs Chrome sessions without clobbering
existing authenticated CDP profiles, and fails fast if the portal login is not
available in the saved environment snapshot.

## Naukri daily profile resume refresh

Before job applies, the Naukri automation must re-upload `Rafi_Resume_Technical_Architect.docx` to the Naukri profile:

```bash
bash scripts/preflight-portal-run.sh naukri
bash scripts/launch-chrome-cdp.sh naukri
node tools/naukri/update_profile_resume.js
```

See STEP 0 in [04-naukri-general.md](04-naukri-general.md).

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
