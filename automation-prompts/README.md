# Job-apply automation prompts (refined)

**This cloud agent cannot write automation Agent instructions** (Automations API is read-only).

**Recommended:** paste the short loaders in [ONE_TIME_LOADERS.md](ONE_TIME_LOADERS.md) once. After that, merge PRs and agents pull the latest full prompts from these files automatically.

Alternatively, paste each file’s full fenced `text` block into the matching automation, then Save.

## Shared targets

| Rule | Value |
| --- | --- |
| Resume | **`resumes/Rafi_Resume.docx`** (bootstrap copies to Documents/resumes) |
| Expected CTC | **65 LPA** (forms always) |
| Current CTC | **52 LPA** |
| Listed max CTC skip | Only if clearly under **35 LPA** |
| Locations | Hyderabad / Telangana **or** Remote / WFH |
| Apply bias | When uncertain on Hyd/remote senior .NET/cloud → **APPLY** |
| Apply paths | Easy/Quick Apply **and** company website / ATS |
| Durable runners | `tools/{linkedin,hitechcity,naukri,cutshort,foundit,instahyre,indeed}/…` |

## First command every run

```bash
bash scripts/preflight-portal-run.sh <portal>
```

Use one of: `linkedin`, `hitechcity`, `foundit`, `cutshort`, `naukri`, `instahyre`, `indeed`.
The preflight bootstraps the resume, syncs Chrome sessions without clobbering
existing authenticated CDP profiles, and fails fast if the portal login is not
available in the saved environment snapshot. `hitechcity` reuses the LinkedIn CDP profile.

## Auto-fix & push (every run)

**Yes — for code-fixable blockers.** Every daily automation must follow
[AUTO_FIX.md](AUTO_FIX.md): patch durable helpers under `tools/` / `scripts/` /
`automation-prompts/`, commit, push a feature branch, open a draft PR into `main`,
and note the fix in [ISSUES_AND_FIXES.md](ISSUES_AND_FIXES.md).

Not auto-fixable from code alone: portal logins/snapshot, Indeed Cloudflare on
public cloud, missing secrets, CAPTCHA/OTP. Those stay owner actions.

## Naukri daily profile resume refresh

Before job applies, the Naukri automation must re-upload `Rafi_Resume.docx` to the Naukri profile. Prefer:

```bash
bash scripts/preflight-portal-run.sh naukri
bash scripts/launch-chrome-cdp.sh naukri
node tools/naukri/daily_apply.js   # runs update_profile_resume.js (STEP 0) then applies
```

Or STEP 0 alone: `node tools/naukri/update_profile_resume.js` (must end with `profileUpdated: true`).

See STEP 0 in [04-naukri-general.md](04-naukri-general.md). Indeed Cloudflare: [INDEED_CLOUDFLARE.md](INDEED_CLOUDFLARE.md).

## Automations

| Automation | Prompt |
| --- | --- |
| LinkedIn Daily 9 AM | [01-linkedin.md](01-linkedin.md) |
| Foundit Daily 9 AM | [02-foundit.md](02-foundit.md) |
| Cutshort Daily 9 AM | [03-cutshort.md](03-cutshort.md) |
| Naukri Daily 9 AM | [04-naukri-general.md](04-naukri-general.md) |
| Instahyre Daily 9 AM | [05-instahyre.md](05-instahyre.md) |
| Indeed Daily (home local) | [06-indeed.md](06-indeed.md) + [INDEED_HOME_AUTOMATION.md](INDEED_HOME_AUTOMATION.md) |
| Notification Job 11 AM | [07-notification.md](07-notification.md) |
| Hitech City / Knowledge City Daily | [08-hitech-city.md](08-hitech-city.md) |

See [ISSUES_AND_FIXES.md](ISSUES_AND_FIXES.md) for what was broken in the last cron and what still needs your login/secrets.
