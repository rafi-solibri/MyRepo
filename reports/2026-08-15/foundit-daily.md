# Foundit daily — 2026-08-15 (post-fix re-run after #160)

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT OK)
- Resume: `resumes/Rafi_Resume.docx`
- Code at start: `ce373d6` (PR #160 ATS completer on main)
- Applied tab: **457 → 457** (+0)
- No `canJobApply` dry-run calls
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`

## Wave 1 — PR #160 primary `.NET` queries
- Applied: **0**
- Duplicates: **42** (already on Foundit via `userJobInfo`)
- Skipped: **496**
- Blocked: **0** (no leftover Workday/company-site ATS jobs)

Eligible `.NET`-token inventory was already applied earlier today. Aveva/Workday cards that #160 targeted are in the duplicate list.

## Wave 2 — extra Arch/Lead queries (this session, unmerged helper)
Ran `tools/foundit/daily_apply.js` with the extra Naukri-parity wave from branch `cursor/foundit-daily-post-fix-re-run-2026-08-15-c3da` after primary exhaustion.

- Applied: **0**
- Duplicates: **88** (42 primary + 46 extra-wave already-applied)
- Skipped: **1322**
- Blocked: **0**

Hyd/India Arch/Lead cards that passed filters were already on the Applied tab. Remaining extra-wave hits were location (Bengaluru/Pune/SG/etc.), no .NET on non-Arch titles, Java/Salesforce-primary, junior bands, or non-software (electrical/civil).

## Applied today (do not re-apply)
Not invented this run. Foundit `userJobInfo` already had today's earlier applies, including:
- relq technologies — Senior .NET Full Stack Developer- India (`62693974`)
- Closeloop Technologies — Web Engineering Manager (`62680103`)
- Kumaran Systems — Lead .Net Developer (`62683340`)
- infomatix web technologies llp — Senior .NET Full Stack Engineer (`62692059`)
- plus prior Falcon applies (TCS Dot NET Full Stack Lead, Mphasis, Aveva, etc.)

## Top skip reasons (extra wave)
- no .NET on title+skills: 411
- location Bengaluru: 202
- no seniority keyword: 113
- location Pune / Singapore / other non-Hyd: remainder
- junior/mid maxExp, SAP, Salesforce, non-software engineering title

## Code fix pushed (PR needs owner create/merge)
Branch: `cursor/foundit-daily-post-fix-re-run-2026-08-15-c3da`

- Extra Raven wave when applies &lt; 8
- Underscore titles + `Dot Net` proof
- Skip Salesforce-primary skills without .NET on title
- Non-India country-only cards no longer inherit JD remote-first/WFH
- Skip electrical/civil/mechanical principals without software/.NET on title
- PR #160 ATS completer kept

`gh pr create` is not permitted from this integration; create the ready PR from the branch and squash-merge so tomorrow's cron has the extra wave. Same-day re-run cap is 2/5 Foundit post-fix jobs so far — do not loop again; inventory is exhausted.

## LinkedIn referral drafts
None — 0 new applies this re-run.
