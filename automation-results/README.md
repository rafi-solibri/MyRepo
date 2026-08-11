# Automation results (machine-written)

Daily JSON summaries published by home/local runners for the Notification Job.

Per portal: `<portal>/YYYY-MM-DD.json` and `<portal>/latest.json`.

Schema counts: `applied`, `external`, `rejected`, `blocked`, `skipped`, `seen`.

```bash
bash scripts/fetch-home-result.sh <portal> --today
```
