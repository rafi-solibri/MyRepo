# Cutshort daily 2026-08-24 IST (post-fix re-run) <!-- pragma: allowlist secret -->

Ran on **main `8709c2c`** (merged resume refresh https://github.com/rafi-solibri/MyRepo/pull/246).
Earlier same-day run did not apply with that resume; this job executed the durable `daily_apply.js` runner with the merged code.

- Login: live candidate dashboard (auth cookie + Matches/Find jobs chrome). Resume: `resumes/Rafi_Resume.docx` (~3.9MB).
- CDP: Chrome 148 on `:9222` with synced portal profile.
- No applications invented. Jobs already applied (none this session) would have been skipped via "view conversation" / already-applied.

## Counts
- Scanned: **3276**
- Qualifying: **0**
- Applied: **0**
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 0 | locked-empty: **0** | verify-empty: 0
- Awaiting listed: 0
- Failures (apply + locked-empty + verify-empty): **0**
- Tailored resumes: built **0** | profile uploaded **0** | upload failed 0
- Q audit skipped (`no_applies_this_session` — historical locked-empty cannot be unlocked)

## Skip taxonomy
- `ctc_under_35`: 1214
- `exp_max_low` (listed max &lt; 6): 1027
- `skip_title` (QA/junior/SAP/Workday/data-title/sales-adjacent): 766
- `location` (not Hyd/Telangana/remote/India-senior): 224
- `no_tier_match` (passed hard skips but not Architect/EM/Lead/.NET/senior-stack): 45

## Why 0 applies (not a new code blocker)
Title scan of Architect / Tech Lead / EM / Staff / .NET cards found **no** Hyd/remote role with listed max CTC ≥ 35L that is also a title-first fit.

Hyd/remote 35L+ title hits were **correct hard-skips**:
- Workday Talent & Performance Lead/Architect (70L, remote)
- Workday Compensation & Benefits Lead/Architect (60L, remote)
- ShopPay Integration Architect (60L, remote)
- Principal Data Engineer / Data Architect / Snowflake Data Architect (35–52L, remote or multi-city incl. Hyd)

High-CTC Engineering Manager / Tech Lead / Staff cards (60–100L) were **Bengaluru-only, remote_not_okay** — location skip per Hyd/remote rule.

Hyd-listed Architect/Lead cards that remain (Technical Architect, Cloud Architect, Tech Lead) have **listed max 18–28L** — skip per “listed max clearly under 35L”.

.NET title hits in this inventory: VB.Net Madurai 32L, ASP.NET Gurugram 15L, .NET Core Navi Mumbai 12L — all location and/or CTC skips.

The 45 `no_tier_match` rows are sales / data-science / PHP / UX / ontologist / robotics — not uncertain Architect/.NET. Loosening classify to “apply all hard-filter-pass” would invent wrong-fit applies.

## Applied
_None_

## Failed applies
_None_

## Auto-fix
No new durable helper change. Post-fix re-run cap not consumed beyond this job (no same-day launch of another apply agent).

Artifact: `/opt/cursor/artifacts/` daily-run JSON (source=cloud, date=2026-08-24, seen=3276, applied=0).
