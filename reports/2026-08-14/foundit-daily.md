# Foundit daily — 2026-08-14

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT OK; `/home/user` confirmed)
- Resume: `resumes/Rafi_Resume.docx`
- First pass Applied tab: **410 → 414** (+4)
- Post-fix re-run (after #140): **414 → 414** (+0) — inventory exhausted / duplicates; Agentforce now skipped as `Salesforce`
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run calls

## Applied (first pass)
1. **Mphasis** — Senior Software Engineer — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4451101638` (`linkedin_no_easy_apply`) — Singapore | remote
2. **Salesforce** — Agentforce - Sucess Architect — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4452468078` (`linkedin_no_easy_apply`) — Hyderabad *(false apply — fixed in #140)*
3. **Tata Consultancy Services** — Dot NET Full Stack Lead — Foundit Falcon `NORMAL` — Hyderabad
4. **Jobgether** — Senior Azure AppDev Architect (Remote) — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4366309400` (`linkedin_no_easy_apply`) — Indonesia | Remote

## Top skip reasons (first pass)
- no .NET on title+skills: 158
- no seniority keyword on title: 107
- location Bengaluru / Pune / other non-Hyd: majority of remainder
- junior/mid maxExp bands / low CTC / WPF / PM

## LinkedIn referral drafts
1. Mphasis — Senior Software Engineer
2. Salesforce — Agentforce *(should not have applied)*
3. TCS — Dot NET Full Stack Lead

## Filter fix
- PR https://github.com/rafi-solibri/MyRepo/pull/140 merged: skip `Agentforce`/`SFDC` titles; skip Salesforce employer when .NET is not on the title.
- Re-run confirmed jobId `62547186` skipped with reason `Salesforce`.
