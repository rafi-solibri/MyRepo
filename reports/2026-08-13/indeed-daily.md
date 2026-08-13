# Indeed Daily — 2026-08-13 (post-fix re-run)

After merge of #132 (volume caps + SmartApply form-fill) + same-day re-run on `main`.

## Counts
- **Submitted (Easy Apply):** 5
- **External opened:** 28
- **Rejected incomplete:** 10
- **Blocked:** 21
- **Skipped:** 43
- **Seen:** 108
- **ok:** True

### vs morning cron
| Metric | Morning | Post-fix re-run |
| --- | ---: | ---: |
| Applied | 5 | 5 |
| External | 0 | 28 |
| Rejected | 8 | 10 |
| Blocked | 0 | 21 |
| Skipped | 27 | 43 |
| Seen | 40 | 108 |

## Applied
- **Workato** — Principal Technical Architect - Hyderabad, Telangana - Indeed.com
- **ITRadiant Solutions Pvt Ltd** — Artificial Intelligence Architect - Hyderabad, Telangana - Indeed.com
- **Axiado** — System Architect - Hyderabad, Telangana - Indeed.com
- **Mattel** — Enterprise Architect - Commercial - Hyderabad, Telangana - Indeed.com
- **SkyLarn AI Technologies Pvt Ltd** — Senior AI Engineer - Gopanpally, Hyderabad, Telangana - Indeed.com

## Notes
- Caps raised: `INDEED_MAX_APPLIES=40`, `INDEED_MAX_SEEN=120` (was 8/40).
- Axiado System Architect + Mattel Enterprise Architect previously `easy_apply_incomplete` — now submitted.
- External company-site opens went from 0 → 28 (still best-effort ATS fill).
- Run hung near the end (~seen 108); artifact finalized after process exit.
- PRs: https://github.com/rafi-solibri/MyRepo/pull/132 , https://github.com/rafi-solibri/MyRepo/pull/133

