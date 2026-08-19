# Cutshort — issues & fixes

## 2026-08-19 (cloud)

| Issue | Fix |
| --- | --- |
| 3189 scanned / 0 qualifying after cloud/SWE classify: remaining Hyd Architect/Lead/.NET titles listed under 35L or Workday/data/Salesforce-primary | no further classify loosening — honor 35L + title-first skips; 5 no_tier leftovers are IT-ops/PLM/HFT/low-YOE backend |
| 2026-08-19 post-fix re-run: leftover 7f43f20 filter fix never reached main so Cloud Engineer/SWE+stack still dropped as no_tier_match (Aug 16: 3202/0) | cherry-pick cloud/SWE classify + foreign-remote skip onto main so today's applies can run |


## 2026-08-16 (cloud)

| Issue | Fix |
| --- | --- |
| 3202 scanned / 0 qualifying: AWS Cloud Engineer + SWE+stack dropped as no_tier_match; Almaty remote_okay leaked | tier1 cloud/AWS engineer; tier3 SWE+stack without senior; skip marketing/data/IAM/Salesforce-primary; reject foreign-only remote |
| daily_apply still hung after browser.disconnect (CDP sockets/handles remain) | process.exit(0) after disconnect on success path (same pattern as naukri) |
| daily_apply.js hung after report: CDP WebSocket kept Node alive (page.close race alone insufficient) | call browser.disconnect() in createCdpSession.disconnect after bounded page.close |


## 2026-08-15 (home)

| Issue | Fix |
| --- | --- |
| session.disconnect page.close() hung after successful scan; HOME_REPORT preferred stale /opt path | Bound page.close with 3s race; prefer cwd artifacts/cutshort-daily-run.json over /opt |
| CDP page/browser closed mid-scan → hard exit 1 with no home report | createCdpSession reconnect + scan/apply retry; never browser.close() on Windows; still write report on closed-page abort |


## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| Final Q audit walked 367 historical awaiting threads (~10 min) after 0 applies | Skip final questionnaire audit when this session applied 0 — locked-empty cannot be unlocked |
| findjobs defaulted to 5/page so inventory stayed thin; Associate Technical Architect hard-skipped | pageSize=50 on /findjobs/q; associate skip allows Technical/Architect/Lead |
| status=external recorded without opening/completing company site | Extract Apply href and completeExternalPage |


## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| FORCE_RESTORE_SESSIONS=1 overwrote live Cutshort auth with stale Aug-6 seed → login_required | ensure-missing defaults FORCE_RESTORE=0; only restore when dest missing auth |
| 0 qualifying after 1100+ scan (India-only .NET/senior cards dropped; exp max 7 for .NET) | Treat India-only senior/.NET as Hyd/remote bias; allow .NET tier2 at maxExp>=6; pull remote_okay pages; log skipReasons |
| CDP page closed during final questionnaire audit → hard exit 1 after scan | Catch TargetClosedError; still write cutshort-daily.md/stats + exit 0 path |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh cutshort "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
