# Automation results (machine-written)

Daily JSON summaries published by home/local runners for the Notification Job.

## Indeed home daily

- `indeed/YYYY-MM-DD.json` — dated snapshot
- `indeed/latest.json` — most recent home run

Schema counts: `applied`, `external`, `rejected`, `blocked`, `skipped`, `seen`.

Fetch from the Notification Job:

```bash
bash scripts/fetch-indeed-home-result.sh
```
