# Foundit daily — 2026-08-19

## Summary
- Logged in: **yes** (MSSOAT + jwtOk; dashboard `/seeker/dashboard`; greeting stayed "Hi, Seeker")
- Resume: `resumes/Rafi_Resume.docx` (17297 bytes; verified by `node tools/foundit/resume.js`)
- Applied tab: **510 → 510** (+0). Intentional logged: **0**
- Skipped: 1195 · Duplicates: 76 · Blocked: 0
- Age window: 1d → **3650d**. Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run. Raven + `classifyJob` + Falcon path only.
- **No invented applies.** Eligible Hyd/remote inventory was already on the Applied tab.

## Candidates by age window
| Window | New cards |
| --- | ---: |
| 1d | 126 |
| 3d | 127 |
| 7d | 330 |
| 14d | 215 |
| 30d | 247 |
| 90d | 189 |
| 3650d | 37 |

## Applied
None this run. Falcon was not called for a new job — every `classifyJob` pass was `userJobInfo` already-applied.

## Top skip reasons
- location not Hyd/remote (Bangalore / Pune / Singapore / Noida / Chennai / …): **565**
- no .NET on title+skills: **344**
- no seniority keyword on title: **106**
- SAP without .NET: **37**
- junior/mid exp bands (max &lt; 10 and min &lt; 8): **56**
- infra/ops, non-software EM, pure AI/data, ServiceNow, presales, low CTC: remainder

Country-only **India** cards (Virtusa `.NET Tech Lead` `61319654`, GSB `.Net Architect` `48081145`, QBurst `Solutions Architect - .Net` `38957799`) were checked via `jobDetail`: locations stay India-centroid and the full JD has no Hyderabad/remote/WFH hit. Skip is correct; not a filter bug.

## Duplicates (already applied — sample of today’s matching inventory)
- relq technologies — Sr .NET Full Stack Developer- India Remote (`63244412`)
- Globallogic Ukraine — Senior .NET Lead (Principal Engineer) (`63102686`)
- ANSR — Principal Engineer - IT Software (.Net) (`62960104`)
- Tata Consultancy Services — Dot NET Full Stack Lead (`62527067`)
- Microsoft Corp — Principal Consultant - Dotnet Full stack & AI (`62054463`)
- Hyland — Senior Software Architect - .NET (`60463983`)
- Persistent Systems — .NET Lead (`60899006`)
- Cimpress — Lead Software Engineer(.Net)-Remote (`34760420`)
- HighLevel — Engineering Manager II (Phone Core / Monetisation / Whatsapp)

## LinkedIn referral drafts
None — no new applies today. Do not invent drafts for skipped or already-applied roles.

## Code fix this run
None. Login, Raven, filters, and Falcon eligibility (`userJobInfo` / `applicationStatus`) behaved as designed. Owner action not required.
