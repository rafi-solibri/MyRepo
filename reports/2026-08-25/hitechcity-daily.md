# Hitech City / Knowledge City daily — 2026-08-25 (post-fix re-run after #263)

## Totals
- **Submitted: 0** | Referrals: 0 | Blocked: 12 | Skipped: 14 | Scanned: 87
- Confirmation-only: every attempt printed `CHAT_NOTIFY NOT_SUBMITTED` — **no invented applies**
- Artifacts written under `/opt/cursor/artifacts/` (daily + careers + discovery + apply-chat)
- Mode: post-fix re-run; careers-only; 10 parallel tabs
- Git: `041cecc` rebuild upload resume from owner master (#263)

## Why this re-run existed
Earlier same-day runs never applied with the merged resume rebuild:
1. Morning cron `bc-a9b4e438` — preflight hirist DEST fix (#257), then handed off (0 submits)
2. Post-fix #1 `bc-375a36cd` — ran on `c507fd2` / #257 (0 submits)
3. Post-fix #2 `bc-d431c064` — ran on `5823080` / #261 compress (0 submits; **#263 not on main yet**)
4. **This run** `bc-34cca19c` — pulled `main` at **#263** and executed careers-only apply

Re-run count today: **3 / 5**. No new code-fixable blocker → no fourth launch.

## Resume (#263 actually used)
- Owner master: `resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx` (3,957,700 B)
- Upload rebuilt: `resumes/Rafi_Resume.docx` (20,945 B) `sha=403c6a36869581a9` (text SHA matched master)
- JD tailor ran before ATS upload (ModMed / Oracle copies under tailored-resumes)

## Phases
| Phase | Result |
| --- | --- |
| Preflight | OK — LinkedIn cookie present; Chrome session synced |
| Chrome CDP | Careers-only: skipped WARP + LinkedIn auto-login; `:9222` ready |
| Discovery | 92 campus tenants (0 added, 92 updated) |
| Careers parallel (10 tabs, 60 companies) | **0 applied** / 12 blocked / 14 skipped / 87 scanned |
| LinkedIn + referrals | skipped (careers-only) — do not wait on LinkedIn CAPTCHA |
| Boards | skipped (careers-only) |

## Submitted
_None._ No ATS confirmation banner (`application submitted` / `thank you for your appl` / iCIMS currently-submitted).

## Careers blocked (12 — owner-only, not code-fixable)
| Company | Role | Reason | Campus |
| --- | --- | --- | --- |
| JPMorgan Chase ×3 | Lead Software Engineer Hyderabad | CAPTCHA/bot wall | Knowledge City / Mindspace |
| Experian ×3 | Lead SWE Mainframe; Director of Engineering; Senior Staff SWE | CAPTCHA/bot wall (SmartRecruiters / DataDome) | Mindspace / Cyber Pearl |
| ModMed ×3 | Principal Cloud Engineer; Senior Software Architect | ATS login wall (Workday `/login`) | Mindspace / Cyber Pearl |
| Oracle ×3 | Senior Principal Forward Deployed Engineer; Principal Core Infrastructure Engineer (×2) | ATS email OTP wall | Knowledge City |

## Skipped (14)
- Intel, Solera — Workday location filter has no Hyderabad facet
- Apple ×4, Goldman Sachs ×4, Meta ×4 — hang-scan hosts
- Optum / UHG — skip-UHG (before parallel fan-out)
- Remaining scanned tenants: 0 matching Hyd EM/Lead/Staff/Principal cards (empty inventory)

## Non-zero inventory (only these reached a real apply attempt)
- JPMorgan Chase: 10 cards → 3 CAPTCHA
- Experian: 8 cards → 3 CAPTCHA
- ModMed: 3 cards → 3 login wall
- Oracle: 3 cards → 3 OTP wall

## Owner actions needed
1. Headed CAPTCHA: JPMC Oracle Cloud + Experian SmartRecruiters (home CDP)
2. ModMed Workday login (session or credentials)
3. Oracle careers email OTP
4. LinkedIn headed login if a later full (non-careers-only) pass is wanted

## Code fix
- **No new helper change.** #263 resume rebuild is on `main` and was used this run.
- Same owner walls as post-fix #1/#2 — auto-fix loop stopped.
