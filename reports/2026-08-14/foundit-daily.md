# Foundit daily — 2026-08-14

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT OK; `/home/user` confirmed)
- Resume: `resumes/Rafi_Resume.docx`
- First pass Applied tab: **410 → 414** (+4)
- Post-fix re-run (after #140): **414 → 414** (+0) — inventory exhausted / duplicates; Agentforce now skipped as `Salesforce`
- Post-fix re-run (after #151 Arch/Lead .NET bypass): **415 → 417** (+2) — `POST_FIX_RERUN=1` on `main` `8e4652a`
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json` (this re-run also copied to `foundit-apply-report-postfix-151.json`)
- No `canJobApply` dry-run calls

## Applied (first pass)
1. **Mphasis** — Senior Software Engineer — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4451101638` (`linkedin_no_easy_apply`) — Singapore | remote
2. **Salesforce** — Agentforce - Sucess Architect — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4452468078` (`linkedin_no_easy_apply`) — Hyderabad *(false apply — fixed in #140)*
3. **Tata Consultancy Services** — Dot NET Full Stack Lead — Foundit Falcon `NORMAL` — Hyderabad
4. **Jobgether** — Senior Azure AppDev Architect (Remote) — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4366309400` (`linkedin_no_easy_apply`) — Indonesia | Remote

## Applied (post-fix re-run after #151)
1. **Sprinto** — Senior Staff Engineer — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4452371012` (`linkedin_no_easy_apply`) — India | remote *(#151 Arch/Lead without .NET-on-skills)*
2. **Deltek** — Accounts Manager (Principal Sales Rep) - North America Sales — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4184584620` (`linkedin_no_easy_apply`) — India | remote *(false apply — bare `principal` rode the Arch/Lead bypass; skip added in follow-up fix)*

## Top skip reasons (first pass)
- no .NET on title+skills: 158
- no seniority keyword on title: 107
- location Bengaluru / Pune / other non-Hyd: majority of remainder
- junior/mid maxExp bands / low CTC / WPF / PM

## Top skip reasons (#151 re-run)
- no .NET on title+skills: 137
- no seniority keyword on title: 108
- location Bengaluru / Pune / Noida / other non-Hyd: majority of remainder
- duplicates already applied today: 38 (Mphasis, TCS .NET Lead, Globallogic Principal Engineer, etc.)
- Agentforce `62547186` still skipped as `Salesforce`

## LinkedIn referral drafts
1. Sprinto — Senior Staff Engineer
2. TCS — Dot NET Full Stack Lead
3. Mphasis — Senior Software Engineer

## Filter fixes
- PR https://github.com/rafi-solibri/MyRepo/pull/140 merged: skip `Agentforce`/`SFDC` titles; skip Salesforce employer when .NET is not on the title.
- PR https://github.com/rafi-solibri/MyRepo/pull/151 merged: Arch/Lead/EM Hyd/remote may pass without .NET on the skills laundry list (Naukri parity).
- Follow-up: skip sales / Accounts Manager / Principal Sales titles; require `principal engineer|architect|…` (not bare `principal`) for the Arch/Lead .NET bypass.
