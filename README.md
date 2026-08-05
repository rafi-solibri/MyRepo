# Job Application Automation (Hyderabad + Remote WFH)

Daily automation that finds roles matching your profile, ranks them, writes application packs, and gives one-click portal search links for **Naukri, LinkedIn, Indeed, Cutshort, Foundit, Instahyre**, and more.

**Target:** Hyderabad + remote WFH · **Expected CTC:** 65 LPA · **Schedule:** every day at **9:00 AM IST** (GitHub Actions).

## What this does / does not do

| Does | Does not |
| --- | --- |
| Pull listings from public APIs (Remotive, RemoteOK, Arbeitnow; optional Adzuna India) | Log into Naukri / LinkedIn / Indeed / Cutshort / Foundit / Instahyre |
| Score jobs against your resume profile | Auto-submit Easy Apply forms |
| Write cover notes + screening answers | Bypass bot protection / scrape behind login |
| Open pre-filtered portal search URLs for you to apply while logged in | Risk your accounts with ToS-violating bots |
| Deduplicate via SQLite tracker + email/Slack digest | |

Auto-apply bots that drive browsers on those portals violate their Terms of Service and commonly get accounts banned. This repo is a **human-in-the-loop** hunter: it does the search/ranking/packaging; you click Apply.

## Resume setup (required)

`Rafi_Resume.docx` was **not present** in this repository when the automation was created. Add your resume text:

```bash
# Option A — paste plain text
cp /path/to/extracted-resume.txt job-automation/data/resume.txt

# Option B — if you have pandoc
pandoc Rafi_Resume.docx -t plain -o job-automation/data/resume.txt
```

Then edit `job-automation/config/profile.yaml` so `skills`, `target_titles`, `experience_years`, and screening answers match the resume.

## Quick start (local)

```bash
cd job-automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

Outputs land in `job-automation/output/`:

- `digest-YYYY-MM-DD.md` — ranked matches + portal links
- `applications/*.md` — per-job cover note + screening checklist
- `jobs.sqlite` — dedupe tracker

## Daily 9 AM IST schedule

GitHub Actions workflow: `.github/workflows/daily-job-hunt.yml`

- Cron: `30 3 * * *` (03:30 UTC = 09:00 IST)
- Also runnable manually via **Actions → Daily Job Hunt → Run workflow**

### Optional secrets (repo → Settings → Secrets)

| Secret | Purpose |
| --- | --- |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | India/Hyderabad listings via [Adzuna developer API](https://developer.adzuna.com/) (free tier) |
| `NOTIFY_WEBHOOK_URL` | Slack or Discord webhook for a short daily ping |
| `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD` `NOTIFY_EMAIL_TO` | Email the markdown digest |

Enable email in `job-automation/config/search.yaml` → `notify.email: true`.

## Portal coverage

Each morning the digest includes deep links for:

- Naukri (Hyderabad + WFH filters)
- LinkedIn (Hyderabad + Remote, past 24h)
- Indeed India
- Cutshort
- Foundit
- Instahyre
- Wellfound
- Hirist

Apply while logged into your own accounts, then mark the checklist inside each application pack.

## Cursor Automation (optional alternative scheduler)

If you prefer Cursor Cloud Automations instead of (or in addition to) GitHub Actions:

1. Open [Cursor Automations](https://cursor.com/automations)
2. Create a daily schedule for **9:00 AM Asia/Kolkata**
3. Prompt the agent with something like:

```text
Run the job hunt in this repo:
  python job-automation/src/main.py --root job-automation
Commit updated digest/tracker if changed. Summarize top 10 new matches
for Hyderabad + remote WFH at ~65 LPA and list portal apply links.
```

## Tuning for 65 LPA

In `config/profile.yaml`:

- `expected_ctc_lpa: 65`
- `min_ctc_lpa: 55` — downranks roles with clearly lower disclosed pay
- Keep titles at senior/staff/lead/architect level

In `config/search.yaml`:

- Raise/lower `min_match_score`
- Edit `search_queries` to your exact specialty (e.g. "Staff Backend Engineer")

## Project layout

```text
job-automation/
  config/profile.yaml    # you + CTC + skills
  config/search.yaml     # queries, sources, portals
  data/resume.txt        # plain-text resume
  src/main.py            # entrypoint
  src/sources/fetchers.py
  src/matcher.py
  src/portals.py
  src/packager.py
  src/tracker.py
  src/notify.py
  output/                # digests, packs, sqlite
.github/workflows/daily-job-hunt.yml
```
