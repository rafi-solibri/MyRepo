# Foundit daily — 2026-08-15 (post-fix re-run after #161)

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT JWT OK; `/seeker/dashboard`)
- Resume: `/workspace/resumes/Rafi_Resume.docx` (52 → 65 LPA)
- Code: `92bb3cc` (PR #161 ATS volume) **plus** extra Arch/Lead query wave (this branch)
- Applied tab: **457 → 457** (+0) — already-applied skipped; no invented applies
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run calls

## Today’s earlier applies (not re-applied)
Morning cron **401 → 405** (+4), all Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `linkedin_no_easy_apply`:

1. **relq technologies** — Senior .NET Full Stack Developer- India — jobId `62693974`
2. **Closeloop Technologies** — Web Engineering Manager — jobId `62680103`
3. **Kumaran Systems** — Lead .Net Developer — jobId `62683340`
4. **infomatix web technologies llp** — Senior .NET Full Stack Engineer — jobId `62692059`

Applied tab later moved **405 → 457** on sibling agents (extra-wave / morning run). This job started at **457** and left it at **457**.

## This re-run
- Primary `.NET` queries + extra Naukri-parity wave (`solution architect`, `technical architect`, `engineering manager`, `technical lead`, …)
- Age windows 1 → 3650
- Intentional applies: **0**
- Duplicates (`userJobInfo`): **88**
- Skipped: **1321**
- Blocked: **0**

Eligible Hyd/remote Arch/Lead/.NET cards that passed `classifyJob` were already on the Applied tab. Remaining hits were location (Bengaluru/Pune/SG/TH/…), no .NET on non-Arch titles, junior/mid bands, SAP, or non-software (electrical/civil).

## Top skip reasons
- no .NET on title+skills: 410
- location Bengaluru: 202
- no seniority keyword on title: 113
- location Pune: 61
- location Singapore: 58 (country-only SG no longer inherits JD “remote-first”)
- maxExp 7&lt;10 junior/mid: 32
- SAP without .NET: 30

## Code fix
Durable extra-wave + location/title hardening is on this branch so tomorrow’s cron does not stop at exhausted `.NET`-token queries. Same-day inventory is exhausted — do not launch another Foundit post-fix loop for this.

## LinkedIn referral drafts (from morning applies only)
1. relq technologies — Senior .NET Full Stack Developer- India — 15+ yrs Solutions Architect / Tech Lead (.NET, Azure/AWS), Hyderabad/remote, immediate. Current 52 LPA → expected 65 LPA.
2. Closeloop Technologies — Web Engineering Manager — same profile; ask HM referral.
3. Kumaran Systems — Lead .Net Developer — same profile; Rafi_Resume.docx.
