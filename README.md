# MyRepo — Daily job-apply agent

Automation artifacts for Mohammed Abdul Rafi Ahmed’s daily .NET leadership job hunt (Hyderabad + remote, ~60 LPA+).

## Layout

- `agent/filters.py` — shared qualification filters (title/skills .NET, seniority, location, exp, CTC)
- `agent/test_filters.py` — unit checks for filter edge cases
- `reports/YYYY-MM-DD/daily-report.md` — per-run application report

## Run notes

Applies require authenticated Naukri / Foundit / LinkedIn sessions. Without secrets or imported browser cookies, the agent scans and reports only — it does not invent submissions.

```bash
python3 agent/test_filters.py
```
