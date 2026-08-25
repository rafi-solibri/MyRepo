# Cutshort daily 2026-08-25

POST_FIX_RERUN=1 after merged fix https://github.com/rafi-solibri/MyRepo/pull/256
(hirist array-slot sync in `scripts/sync-chrome-sessions.sh`). Ran on
`origin/main` @ `6f1901b` with `resumes/Rafi_Resume.docx`. Preflight + Chrome CDP
auth OK. Durable runner: `node tools/[portal]/daily_apply.js`.

## Counts
- Scanned: **3270**
- Qualifying: **0**
- Applied: **0**
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 0 | locked-empty: **0** | verify-empty: 0
- Awaiting listed: 0
- Failures (apply + locked-empty + verify-empty): **0**
- Tailored resumes: built **0** | profile uploaded **0** | upload failed 0

## Skip taxonomy (not invented applies)
- `ctc_under_35`: 1214
- `exp_max_low` (listed max exp under 6): 1015
- `skip_title` (QA/junior/SAP/Workday/data-title/sales/etc.): 770
- `location` (not Hyd/Telangana/remote/India-senior bias): 225
- `no_tier_match` (passed hard skips, not Architect/EM/Lead/Senior .NET/cloud): 46

The 46 leftover titles were inspected: data/ML, sales/marketing, PHP, Salesforce,
Oracle MDM/ERP, ServiceNow, robotics, UX, ontologist, CAD/CAM, customer-success,
presales. None were Hyd/remote Architect / Tech Lead / EM / Principal / Staff /
Senior .NET-cloud. No filter auto-fix; do not invent applies.

## Applied
_None_

## Failed applies
_None_
