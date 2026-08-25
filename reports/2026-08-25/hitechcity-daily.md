# Hitech City / Knowledge City daily — 2026-08-25 (post-fix re-run #2)

## Status
**Careers-only run completed on merged `main` (`5823080`, #261 resume compress).** Confirmation applies only — **0 submitted**. None invented.

This is same-day post-fix re-run **2 / 5**. Earlier morning automation (`bc-a9b4e438`) was killed after merging #257. First post-fix re-run (`bc-375a36cd` on `c507fd2`) also submitted 0. This run used the later merged #261 code.

## Totals
| Metric | Count |
| --- | ---: |
| Submitted (confirmation text) | **0** |
| Referrals | 0 |
| Blocked | 7 |
| Skipped | 14 |
| Careers scanned | 91 |
| Discovery | 92 tenants (0 added, 92 updated) |
| Parallel tabs | 10 |

- Mode: `POST_FIX_RERUN=1` `HITECHCITY_CAREERS_ONLY=1` `HITECHCITY_PARALLEL_TABS=10`
- Head: `5823080 fix(naukri): compress resume under 2MB and harden profile STEP 0 (#261)`
- Resume: `resumes/Rafi_Resume.docx` (20 945 bytes after #261 compress; content intact)
- Preflight: OK (`li_at` present). Chrome CDP launched **without** WARP / LinkedIn auto-login.
- LinkedIn + boards: skipped (careers-only, as instructed — do not wait on LinkedIn CAPTCHA)
- Runtime: 2026-08-25 03:59:52Z → 04:04:29Z (EXIT:0)

## Applied (confirmation text)
**None.** No `CHAT_NOTIFY SUBMITTED`. No ATS “application submitted” / “thank you for applying” banners.

## Not submitted (owner walls)
| Company | Role | Reason |
| --- | --- | --- |
| JPMorgan Chase ×3 | Lead Software Engineer Hyderabad | CAPTCHA/bot wall (Oracle Cloud HCM) |
| Experian | Solutions Architect · Hyderabad, India | CAPTCHA/bot wall (SmartRecruiters / DataDome) |
| ModMed ×3 | Principal Cloud Engineer / Senior Software Architect (Hyd) | `ats_login_wall` (Workday `/login`) |

## Skipped
- `skip_uhg`: Optum, UnitedHealth Group
- `workday_no_hyderabad_facet`: Intel, Solera
- `hang_scan_host`: Apple, Goldman Sachs, Meta (4 keyword URLs each)

## Inventory notes (not a new code regression)
- Many catalog tenants still have empty `careersUrls` → `CAREERS SCAN … urls=0` (same 2026-08-21 / first-rerun pattern).
- Portals that had search URLs mostly extracted **0 matching Hyd cards** after location pin (Hyland, Cognizant, Accenture, Oracle, Blue Yonder, GE Vernova, AMD, IBM, Salesforce, …). Only JPMC / Experian / ModMed produced apply attempts.
- Already-applied today: **nothing to skip** (0 confirmed submits from morning or first re-run).

## Code fix
- Consumed merged **#261** (Naukri/shared resume compress under 2 MB). Tailored resume files were written for ModMed and Experian before those walls.
- **No new code-fixable blocker** this run. CAPTCHA / Workday login are owner-only. Did **not** launch another post-fix re-run (cap 5; used 2).

## Owner actions
1. Headed CAPTCHA for JPMC Oracle Cloud + Experian SmartRecruiters: `bash scripts/home-headed-login.sh hitechcity` (or sit on the focused ASK_OWNER tab).
2. ModMed Workday login / guest apply credentials.
3. LinkedIn live session if a later non-careers-only pass is wanted (`LINKEDIN_PASSWORD` / headed login). Hirist cookies remain missing (not used this phase).

## Artifacts
- `/opt/cursor/artifacts/hitechcity-daily.json`
- `/opt/cursor/artifacts/hitechcity-careers.json` (+ `hitechcity-careers-w0.json` … `w9.json`)
- `/opt/cursor/artifacts/hitechcity-apply-chat.jsonl`
- `/opt/cursor/artifacts/hitechcity-daily-run.log`
- `/opt/cursor/artifacts/hitechcity-discovery.json`
- Copies under `reports/2026-08-25/`
