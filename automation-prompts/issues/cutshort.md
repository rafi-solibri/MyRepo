# Cutshort — issues & fixes

## 2026-08-25 (cloud)

| Issue | Fix |
| --- | --- |
| sync-chrome-sessions.sh: PORTALS included hirist but DESTS/COOKIE_SETS/REQUIRED omitted it — DESTS[$i] unbound after indeed (preflight exit 1; also mis-synced hirist onto linkedin-alt path) | Aligned arrays: add hirist dest via chrome_session path + token cookie; linkedin_alt remains last optional (REQUIRED 0 0 for hirist/linkedin_alt until seed has hirist token) |


## 2026-08-24 (cloud)

| Issue | Fix |
| --- | --- |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-24) | Replaced master + Rafi_Resume.docx alias; JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 late) | Replaced master + Rafi_Resume.docx alias (~3.9MB); JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 evening) | Replaced resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx + Rafi_Resume.docx alias; JD tailor still runs on top; upload filename stays Rafi_Resume |


## 2026-08-23 (cloud)

| Issue | Fix |
| --- | --- |
| Owner supplied new master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx | Synced into resumes/Rafi_Resume.docx (+ Architect alias); bootstrap prefers owner-named file; JD tailor still runs on top; upload filename/label stays Rafi_Resume |


## 2026-08-20 (cloud)

| Issue | Fix |
| --- | --- |
| Applies rejected by AI/manual — same generic Rafi_Resume.docx + generic note for every JD | Reuse shared tools/resume_tailor.js; daily_apply uploads tailored docx via Update resume before each apply + external ATS; JD-keyword notes |


## 2026-08-16 (cloud)

| Issue | Fix |
| --- | --- |
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
