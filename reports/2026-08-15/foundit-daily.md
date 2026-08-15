# Foundit daily — 2026-08-15 (post-fix re-run after #162)

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT / JWT OK; dashboard confirmed)
- Resume: `resumes/Rafi_Resume.docx` (never invented; no Architect stub required)
- This re-run Applied tab: **457 → 457** (+0)
- Intentional applies this session: **0** (do not invent applies)
- Duplicates skipped via `userJobInfo`: **42**
- Filter skips: **496**
- Blocked: **0**
- Age window expanded through 3650d; candidates: d1=46, d3=41, d7=66, d14=127, d30=135, d90=110, d3650=13
- Head: `2140d75` — `fix(ats): submit company-site applies instead of timing out on hops` (#162)
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run calls

## Why +0 on this re-run
Eligible Hyd/remote .NET Architect / Lead / EM inventory was already on the Applied tab from today's earlier Foundit runs. `daily_apply.js` skipped those as `userJobInfo` duplicates. No leftover Workday/company-site ATS cards remained for #162 to complete (Aveva / prior ATS hops already registered on Foundit).

## Applied this session
None.

## Already applied today (skipped, not re-submitted)
Primary `.NET` query hits already on Applied tab include (sample):
- relq technologies — Senior .NET Full Stack Developer- India
- Closeloop Technologies — Web Engineering Manager
- Kumaran Systems — Lead .Net Developer
- infomatix web technologies llp — Senior .NET Full Stack Engineer
- Tata Consultancy Services — Dot NET Full Stack Lead
- embrace software inc — Lead Engineer/ Architect (.NET)
- Microsoft Corp — Principal Consultant - Dotnet Full stack & AI
- Hyland — Senior Software Architect - .NET
- Persistent Systems — .NET Lead
- Cimpress — Lead Software Engineer(.Net)-Remote
- Cubic Transportation Systems — Principal Software Engineer (.Net)
- The Wells Fargo Foundation — Principal Engineer - .NET Core / GenAI

## Top skip reasons
- no .NET on title+skills: 138
- no seniority keyword on title: 105
- location Bengaluru: 74 (+ other non-Hyd cities)
- junior/mid maxExp bands / low listed CTC / WPF / SAP / Salesforce

## LinkedIn referral drafts
None this re-run (0 new applies).

## Auto-fix
No new code-fixable blocker. Did not launch another post-fix re-run (already inside POST_FIX_RERUN=1; cap 5).
